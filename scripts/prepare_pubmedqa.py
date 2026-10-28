"""Add PubMed research abstracts to the knowledge base, from PubMedQA.

Input:  data/raw/pubmedqa/ori_pqal.json
        (download: https://raw.githubusercontent.com/pubmedqa/pubmedqa/master/data/ori_pqal.json)
Output: data/processed/research.jsonl  (one passage per line)

Run from the project folder:  python scripts/prepare_pubmedqa.py

PubMedQA (Jin et al., 2019, MIT licence) has 1,000 research questions, each
with a PubMed abstract, the MeSH terms PubMed gave that article, the abstract's
conclusion, and an expert yes/no/maybe answer.

These passages are kept SEPARATE from the patient passages (corpus.jsonl):
they are written for researchers, so MedQuery must not quote them to patients
as plain advice. They are research evidence, shown as such.
"""
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw" / "pubmedqa" / "ori_pqal.json"
OUT = ROOT / "data" / "processed" / "research.jsonl"

LICENCE = "MIT (PubMedQA, Jin et al. 2019); abstract text belongs to its publisher, used for education"


def clean(text: str) -> str:
    return " ".join(text.split())


def main() -> None:
    if not RAW.exists():
        raise SystemExit(
            f"PubMedQA not found at {RAW}.\nDownload it with:\n"
            "curl -L --create-dirs -o data/raw/pubmedqa/ori_pqal.json "
            "https://raw.githubusercontent.com/pubmedqa/pubmedqa/master/data/ori_pqal.json"
        )

    data = json.loads(RAW.read_text(encoding="utf-8"))
    rows, skipped, decisions = [], 0, Counter()
    for pmid, item in data.items():
        question = clean(item.get("QUESTION") or "")
        contexts = [clean(c) for c in item.get("CONTEXTS") or [] if c and c.strip()]
        conclusion = clean(item.get("LONG_ANSWER") or "")
        mesh = [m for m in item.get("MESHES") or [] if m]
        if not (question and contexts and conclusion and mesh):
            skipped += 1
            continue
        decision = item.get("final_decision", "")
        decisions[decision] += 1
        rows.append({
            "id": f"PubMedQA_{pmid}",
            "title": question,
            # The abstract without its conclusion, then the conclusion, labelled.
            "text": " ".join(contexts) + " Conclusion: " + conclusion,
            "question": question,
            "conclusion": conclusion,
            "decision": decision,          # expert answer: yes / no / maybe
            "year": item.get("YEAR") or "",
            "topic": mesh[0],              # first MeSH heading PubMed gave the article
            "mesh_terms": mesh,
            "source": "PubMed abstract (via PubMedQA)",
            "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            "licence": LICENCE,
            "collection": "research",
        })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    words = sum(len(r["text"].split()) for r in rows)
    print(f"Wrote {len(rows)} research passages to {OUT.relative_to(ROOT)}")
    print(f"Skipped {skipped} incomplete items")
    print(f"Expert answers: {dict(decisions)}")
    print(f"Average length: {words / len(rows):.0f} words")


if __name__ == "__main__":
    main()