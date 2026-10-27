"""Build a patient-friendly answer from retrieved passages (owner: Member 3).

This is EXTRACTIVE: every sentence in the answer is copied word for word from
a retrieved passage and carries the number of that passage in the source list.
We never write new medical claims, so we cannot invent facts. We can still pick
a sentence that is relevant but incomplete, or that is out of date; the
confidence score does not protect against that.
"""
import re

from app import retrieval

# Confidence thresholds on retrieval.coverage() (0..1), chosen on 14 test
# questions plus 18 tuning questions (10 on-topic, 8 off-topic). Re-check them
# whenever the corpus or retrieval changes.
# When the question names a condition we recognise:
ANSWERED = 0.6   # at or above: "answered"
LOW = 0.4        # between LOW and ANSWERED: "low_confidence"; below: "no_evidence"
# When it names no recognised condition, it can never be "answered":
NO_TOPIC_LOW = 0.6  # at or above: "low_confidence"; below: "no_evidence"

MAX_PASSAGES = 3
MAX_SENTENCES = 4
PER_PASSAGE = 2
MIN_WORDS, MAX_WORDS = 6, 60

# Our sources are American; their emergency number would mislead users in India.
# Emergency advice comes only from app/safety.py.
SKIP = re.compile(r"\b911\b")

PERSONAL = re.compile(
    r"\b(do i have|have i got|am i|is my|does my|should i take|what should i take|what dose)\b",
    re.IGNORECASE,
)
PERSONAL_NOTE = (
    "I can't tell whether this applies to you. Only a doctor who examines you "
    "can diagnose you or advise on your treatment."
)
LOW_CONFIDENCE_NOTE = (
    "My sources only partly match your question, so please check this with a doctor."
)


def split_sentences(text: str) -> list[str]:
    """Cut a passage into sentences and bullet points. Each piece is an exact
    substring of the passage, so it can be checked against the source."""
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z(])|\s+-\s+(?=[A-Z])", text)
    return [p.strip() for p in parts if p.strip()]


def _sentence_score(words: set[str], sentence: str) -> float:
    present = set(retrieval.tokenize(sentence))
    return sum(retrieval.idf(w) for w in words if w in present)


def build(words: list[str], passages: list[dict]) -> tuple[str, list[dict]]:
    """Return (answer_markdown, passages_used). Citation [n] = passages_used[n-1]."""
    # Answer about one condition at a time: the best passage's topic.
    topic = passages[0]["topic"].lower()
    chosen = [p for p in passages if p["topic"].lower() == topic][:MAX_PASSAGES]

    query = set(words)
    candidates = []  # (score, passage_rank, position, sentence)
    for rank, p in enumerate(chosen):
        for pos, s in enumerate(split_sentences(p["text"])):
            if MIN_WORDS <= len(s.split()) <= MAX_WORDS:
                bonus = 0.5 if pos == 0 else 0.0  # opening sentences usually define the topic
                candidates.append((_sentence_score(query, s) + bonus, rank, pos, s))

    picked, per_passage, seen = [], {}, set()
    for score, rank, pos, s in sorted(candidates, key=lambda c: -c[0]):
        if score <= 0 or per_passage.get(rank, 0) >= PER_PASSAGE:
            continue
        if s.lower() in seen or SKIP.search(s):  # same sentence in two passages; US-only advice
            continue
        seen.add(s.lower())
        picked.append((rank, pos, s))
        per_passage[rank] = per_passage.get(rank, 0) + 1
        if len(picked) == MAX_SENTENCES:
            break
    if not picked:
        return "", []

    # Number only the passages we actually quote, in order of relevance.
    used_ranks = sorted({rank for rank, _, _ in picked})
    number = {rank: n for n, rank in enumerate(used_ranks, 1)}
    lines = [f"- {s} [{number[rank]}]" for rank, pos, s in sorted(picked)]
    answer = f"Here is what my sources say about **{chosen[0]['topic']}**:\n\n" + "\n".join(lines)
    return answer, [chosen[r] for r in used_ranks]
