"""Medical passage retrieval with BM25 (owner: Member 3).

BM25 in one paragraph: a passage scores high when it contains the question's
words, especially RARE words (a word found in few passages, like "asthma",
counts more than a common word like "disease"), and short passages that
contain the words beat long ones that mention them once. It matches words,
not meaning: "heart attack" and "myocardial infarction" do not match on their
own. MeSH synonyms (expand_with_mesh) close part of that gap; semantic search
(next milestone) closes more.

The index is built once, the first time search() is called (a few seconds).
"""
import difflib
import json
import math
from collections import Counter
from functools import lru_cache
from pathlib import Path

from rank_bm25 import BM25Okapi

from app import mesh
from app.preprocess import tokenize

CORPUS = Path(__file__).resolve().parent.parent / "data" / "processed" / "corpus.jsonl"

# Words that say nothing about WHICH condition is meant ("Is it serious?").
# A question made only of these cannot be answered from evidence.
# (Passed through tokenize() so they match lemmatised questions.)
GENERIC = set(tokenize("""
serious dangerous bad normal worse better ok okay safe common rare problem problems
help happen happens mean means know tell thing things
"""))


# Words that say what KIND of question it is, not what it is about. They help
# BM25 rank passages, but the evidence check (coverage) ignores them: a diabetes
# passage that says "signs and symptoms" answers "warning signs of diabetes".
QUESTION_CUES = set(tokenize("""
symptom symptoms sign signs warning early cause causes caused why risk risks chance chances
treat treats treated treatment treatments cure cured manage managed therapy done
prevent prevents prevented prevention avoid lower reduce stop
diagnose diagnosed diagnosis test tests tested find out tell
"""))

@lru_cache(maxsize=1)
def _index() -> tuple[list[dict], BM25Okapi]:
    if not CORPUS.exists():
        raise RuntimeError(f"{CORPUS} not found. Run scripts/prepare_corpus.py first.")
    with CORPUS.open(encoding="utf-8") as f:
        passages = [json.loads(line) for line in f]
    # Index the title (topic + MedQuAD question) together with the passage text.
    docs = [tokenize(p["title"] + " " + p["text"]) for p in passages]
    return passages, BM25Okapi(docs)


KNOWN_MIN = 2      # a word in 2+ passages is a real word (1 may be a typo in the source)
CORRECT_MIN = 50   # we correct TO common words, so "covid" never becomes "cvid" ...
RARE_CLOSENESS = 0.88  # ... or to rarer medical words only when the spelling is very close
                       # ("infraction" -> "infarction" is 0.90; "engine" -> "engineer" is 0.86)


@lru_cache(maxsize=1)
def _common_words() -> list[str]:
    """Words a typo may be corrected to: common corpus words, plus rarer corpus
    words that are part of a MeSH medical term ("infarction" is in only a few
    passages but is a real medical word)."""
    medical = {w for term in mesh._load()["terms"] for w in tokenize(term)}
    return [w for w, df in _doc_freq().items()
            if df >= CORRECT_MIN or (df >= KNOWN_MIN and w in medical)]


@lru_cache(maxsize=1)
def _doc_freq() -> dict[str, int]:
    passages, _ = _index()
    freq: dict[str, int] = {}
    for p in passages:
        for w in set(tokenize(p["title"] + " " + p["text"])):
            freq[w] = freq.get(w, 0) + 1
    return freq


def warm_up() -> None:
    """Build the index and word counts (about 2 seconds)."""
    _index()
    _common_words()
    _topics()
    _concept_topics()


def correct(query: str) -> tuple[list[str], list[str]]:
    """Fix spelling against the corpus vocabulary.

    Returns (words, unknown): the corrected words, and the words that are not
    in our sources at all even after correction (e.g. "semaglutide", "covid").
    """
    freq = _doc_freq()
    words, unknown = [], []
    for w in tokenize(query):
        if freq.get(w, 0) >= KNOWN_MIN or w.isdigit():
            words.append(w)
            continue
        # Of the close spellings with the same first letter ("cricket" never becomes
        # "rickets"), take the closest; if two are equally close, the more common one
        # ("infraction" -> "infarction", not "information"; "diabetis" -> "diabetes").
        same_start = [c for c in _common_words() if c[0] == w[0]]
        def closeness(c: str) -> tuple[float, int]:
            return round(difflib.SequenceMatcher(None, w, c).ratio(), 2), freq[c]

        close = [c for c in difflib.get_close_matches(w, same_start, n=10, cutoff=0.8)
                 if freq[c] >= CORRECT_MIN or closeness(c)[0] >= RARE_CLOSENESS]
        if close:
            words.append(max(close, key=closeness))
        else:
            words.append(w)
            unknown.append(w)
    return words, unknown


def idf(word: str) -> float:
    """How rare a word is in the corpus. Unknown words get the highest weight,
    because a word we have never seen (e.g. a new drug name) is exactly the
    part of the question we have no evidence for."""
    bm25 = _index()[1]
    if word in bm25.idf:
        return max(bm25.idf[word], 0.0)
    return math.log(bm25.corpus_size + 1)


def coverage(query_words: list[str], passage: dict) -> float:
    """Share of the question's important words that appear in the passage,
    weighted by rarity. 1.0 = every important word is present.
    Question-type words (QUESTION_CUES) are left out unless there is nothing else."""
    subject = set(query_words) - QUESTION_CUES or set(query_words)
    if not subject:
        return 0.0
    present = set(tokenize(passage["title"] + " " + passage["text"]))
    total = sum(idf(w) for w in subject)
    found = sum(idf(w) for w in subject if w in present)
    return found / total if total else 0.0


def is_generic(query: str) -> bool:
    """True when the question names no condition, symptom or treatment."""
    words = tokenize(query)
    return not words or all(w in GENERIC for w in words)


@lru_cache(maxsize=1)
def _topics() -> dict[str, tuple[frozenset, list[int]]]:
    """Topic name (lower case) -> (its words, indexes of its passages)."""
    topics: dict[str, tuple[frozenset, list[int]]] = {}
    by_words: dict[frozenset, str] = {}
    for i, p in enumerate(_index()[0]):
        name = p["topic"].lower()
        words = frozenset(tokenize(name))
        # Topics that are the same words after lemmatisation are one topic:
        # "Kidney Disease" and "Kidney Diseases" share their passages.
        name = by_words.setdefault(words, name) if words else name
        if name not in topics:
            topics[name] = (words, [])
        topics[name][1].append(i)
    return topics


def find_topic(words: list[str]) -> str | None:
    """The condition the question names, matched against our corpus topic names.

    "warning signs of diabetes" -> "diabetes". If several topics fit, the most
    specific wins (rarest words): "high blood pressure" beats "pressure", and
    "measles" beats "fever". A simple dictionary match, not a trained model.
    """
    query = set(words)
    best, best_weight = None, 0.0
    for name, (topic_words, _) in _topics().items():
        if topic_words and topic_words <= query:
            weight = sum(idf(w) for w in topic_words)
            if weight > best_weight:
                best, best_weight = name, weight
    return best


@lru_cache(maxsize=1)
def _concept_topics() -> dict[str, str]:
    """MeSH id -> the corpus topic that IS that concept ("D009203" -> "heart attack")."""
    topics = _topics()
    out: dict[str, str] = {}
    for name, (_, idx) in topics.items():
        found = mesh.find(name)
        if len(found) == 1 and found[0]["text"].lower() == name:
            ui = found[0]["ui"]
            if ui not in out or len(idx) > len(topics[out[ui]][1]):
                out[ui] = name
    return out


@lru_cache(maxsize=1)
def _concept_counts() -> Counter:
    """How many patient passages are tagged with each MeSH id."""
    return Counter(ui for p in _index()[0] for ui in p.get("mesh_ids", []))


def expand_with_mesh(words: list[str], unknown: list[str], entities: list[dict]) -> tuple[list[str], list[str]]:
    """Search for each MeSH concept the question names by the corpus's own name.

    "paracetamol" -> "acetaminophen" (our US sources' word);
    "myocardial infarction" -> "heart attack" (our topic name).
    The user's words are REPLACED, so the evidence check does not count them as
    missing from passages that use the other name. A word we never saw stops
    being "unknown" when it belongs to a concept our passages cover. Concepts
    with no passages (e.g. COVID-19) change nothing.
    """
    freq = _doc_freq()
    words, unknown = list(words), list(unknown)
    for e in entities:
        if not _concept_counts().get(e["mesh_id"]):
            continue
        alias = [w for w in tokenize(_concept_topics().get(e["mesh_id"], e["name"]))
                 if freq.get(w, 0) >= KNOWN_MIN]
        own = set(tokenize(e["text"]))
        if not alias or set(alias) == own:
            continue
        kept = [w for w in words if w not in own]
        words = kept + [w for w in alias if w not in kept]
        unknown = [w for w in unknown if w not in own]
    return words, unknown


# NLU intent -> MedQuAD question type, used to prefer passages of the right kind.
INTENT_QTYPE = {
    "symptoms": "symptoms", "treatment": "treatment", "prevention": "prevention",
    "causes": "causes", "diagnosis": "exams and tests",
}


def search(query: str, k: int = 5, intent: str | None = None) -> list[dict]:
    """Return up to k passages, best first. The query should already be
    spell-corrected (see correct()).

    If the question names a condition in our corpus, only that condition's
    passages are searched. If the intent is known (from app/nlu.py), passages
    of the matching question type are preferred.

    Each passage: {"id", "title", "source", "url", "text", "topic", "qtype",
                   "score", "coverage"}
    """
    passages, bm25 = _index()
    words = tokenize(query)
    if not words:
        return []
    scores = bm25.get_scores(words)

    topic = find_topic(words)
    pool = _topics()[topic][1] if topic else range(len(passages))
    qtype = INTENT_QTYPE.get(intent or "")
    ranked = []
    for i in pool:
        if scores[i] <= 0:
            continue
        boost = 1.5 if qtype and passages[i].get("qtype") == qtype else 1.0
        ranked.append((scores[i] * boost, i))
    ranked.sort(reverse=True)

    results = []
    for score, i in ranked[:k]:
        p = passages[i]
        results.append({
            "id": p["id"], "title": p["title"], "source": p["source"], "url": p["url"],
            "text": p["text"], "topic": p["topic"], "qtype": p.get("qtype", ""),
            "score": round(float(score), 3),
            "coverage": round(coverage(words, p), 3),
        })
    return results
