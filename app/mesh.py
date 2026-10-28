"""Find MeSH concepts in text (medical entity normalisation).

Used by scripts/tag_mesh.py to tag the knowledge base, and later by the
chatbot to understand which conditions, drugs and procedures a question names.

    >>> from app import mesh
    >>> mesh.find("Can paracetamol help after a heart attack?")
    [{'ui': 'D000082', 'name': 'Acetaminophen', 'branch': 'drug or chemical', 'text': 'paracetamol'},
     {'ui': 'D009203', 'name': 'Myocardial Infarction', 'branch': 'disease', 'text': 'heart attack'}]

How: slide over the words and look up the longest phrase (up to MAX_WORDS
words) that is a known term, so "high blood pressure" wins over "pressure".
It is a dictionary match: it does not understand negation ("no fever") or
words it has never seen.
"""
import json
import re
from functools import lru_cache
from pathlib import Path

DICTIONARY = Path(__file__).resolve().parent.parent / "data" / "processed" / "mesh_terms.json"
MAX_WORDS = 6

WORD = re.compile(r"[A-Za-z0-9]+(?:['\-][A-Za-z0-9]+)*")


@lru_cache(maxsize=1)
def _load() -> dict:
    if not DICTIONARY.exists():
        raise RuntimeError(f"{DICTIONARY} not found. Run scripts/build_mesh.py first.")
    return json.loads(DICTIONARY.read_text(encoding="utf-8"))


def find(text: str) -> list[dict]:
    """Every MeSH concept named in the text, in order, each once."""
    data = _load()
    terms, acronyms, concepts = data["terms"], data["acronyms"], data["concepts"]
    words = WORD.findall(text)
    found, seen, i = [], set(), 0
    while i < len(words):
        match = None
        for n in range(min(MAX_WORDS, len(words) - i), 0, -1):
            phrase = " ".join(words[i:i + n])
            ui = terms.get(phrase.lower()) or (acronyms.get(phrase) if n == 1 else None)
            if ui:
                match = (ui, phrase, n)
                break
        if match:
            ui, phrase, n = match
            if ui not in seen:
                seen.add(ui)
                found.append({"ui": ui, **concepts[ui], "text": phrase})
            i += n
        else:
            i += 1
    return found