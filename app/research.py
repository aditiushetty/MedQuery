"""Related research from the PubMed abstracts (PubMedQA) in the knowledge base.

A study is related when it is ABOUT a condition, drug or disorder the question
names. We match MeSH ids, scoring each concept:
  +3  PubMed's own indexers listed it for the article (it is a main subject)
  +2  the study's research question names it
A study needs at least 5 points (so one concept on both counts) to be shown.

These are research findings from particular study groups, not advice for one
person, so the chatbot shows them separately and labels them as research.
"""
import json
from functools import lru_cache
from pathlib import Path

from app import mesh

RESEARCH = Path(__file__).resolve().parent.parent / "data" / "processed" / "research.jsonl"
MIN_SCORE = 5
BRANCHES = {"disease", "mental disorder", "drug or chemical"}  # not procedures


@lru_cache(maxsize=1)
def _studies() -> list[dict]:
    if not RESEARCH.exists():
        return []  # the chatbot works without the research file
    by_name = {c["name"]: ui for ui, c in mesh._load()["concepts"].items()}
    studies = []
    with RESEARCH.open(encoding="utf-8") as f:
        for line in f:
            s = json.loads(line)
            s["_indexed"] = {by_name[t] for t in s["mesh_terms"] if t in by_name}
            s["_in_question"] = {c["ui"] for c in mesh.find(s["title"])}
            studies.append(s)
    return studies


def related(entities: list[dict], k: int = 2) -> list[dict]:
    """Up to k studies about the question's concepts, most relevant first, then newest."""
    ids = {e["mesh_id"] for e in entities if e.get("label") in BRANCHES}
    if not ids:
        return []
    scored = []
    for s in _studies():
        score = sum(3 * (i in s["_indexed"]) + 2 * (i in s["_in_question"]) for i in ids)
        if score >= MIN_SCORE:
            scored.append((score, s["year"], s))
    scored.sort(key=lambda t: (t[0], t[1]), reverse=True)
    return [
        {"id": s["id"], "question": s["question"], "decision": s["decision"],
         "conclusion": s["conclusion"], "year": s["year"], "url": s["url"]}
        for _, _, s in scored[:k]
    ]
