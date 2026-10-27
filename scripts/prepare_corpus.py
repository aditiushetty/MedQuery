"""Build the MedQuery knowledge base from MedQuAD (owner: Member 1).

Input:  data/raw/medquad/   (git clone https://github.com/abachaa/MedQuAD.git data/raw/medquad)
Output: data/processed/corpus.jsonl  (one passage per line)

Run from the project folder:  python scripts/prepare_corpus.py

What it does:
1. Reads every XML file in the MedQuAD folders that still have answers.
   (MedQuAD removed the answers from 3 MedlinePlus folders for copyright reasons,
   so we skip ADAM, MPlusDrugs and MPlusHerbsSupplements.)
2. Cleans the answer text (whitespace, empty answers).
3. Splits long answers into passages of at most MAX_WORDS words, at paragraph
   boundaries where possible, so a search hit points at a readable chunk.
4. Drops exact duplicate passages (some answers repeat across sources).
5. Writes one JSON object per passage, with source and licence metadata.
"""
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw" / "medquad"
OUT = ROOT / "data" / "processed" / "corpus.jsonl"

MAX_WORDS = 200
MIN_WORDS = 5
LICENCE = "CC BY 4.0 (MedQuAD, Ben Abacha & Demner-Fushman 2019)"

# Folder in MedQuAD -> readable name of the original NIH website
SOURCES = {
    "1_CancerGov_QA": "National Cancer Institute (cancer.gov)",
    "2_GARD_QA": "Genetic and Rare Diseases Information Center (GARD)",
    "3_GHR_QA": "Genetics Home Reference (NLM)",
    "4_MPlus_Health_Topics_QA": "MedlinePlus Health Topics",
    "5_NIDDK_QA": "NIDDK (niddk.nih.gov)",
    "6_NINDS_QA": "NINDS (ninds.nih.gov)",
    "7_SeniorHealth_QA": "NIHSeniorHealth",
    "8_NHLBI_QA_XML": "NHLBI (nhlbi.nih.gov)",
    "9_CDC_QA": "CDC (cdc.gov)",
}


def clean(text: str) -> str:
    """Collapse runs of spaces/tabs, keep paragraph breaks."""
    paragraphs = [" ".join(p.split()) for p in re.split(r"\n\s*\n", text)]
    return "\n\n".join(p for p in paragraphs if p)


def split_passages(text: str) -> list[str]:
    """Group paragraphs into passages of at most MAX_WORDS words.

    A single paragraph longer than MAX_WORDS is cut at sentence ends.
    """
    pieces = []
    for para in text.split("\n\n"):
        if len(para.split()) <= MAX_WORDS:
            pieces.append(para)
        else:
            pieces.extend(re.split(r"(?<=[.!?])\s+", para))

    passages, current = [], []
    for piece in pieces:
        if current and len(" ".join(current + [piece]).split()) > MAX_WORDS:
            passages.append(" ".join(current))
            current = []
        current.append(piece)
    if current:
        passages.append(" ".join(current))
    return passages


def read_folder(folder: Path) -> list[dict]:
    rows = []
    for path in sorted(folder.glob("*.xml")):
        doc = ET.parse(path).getroot()
        focus = (doc.findtext("Focus") or "").strip()
        if not focus:  # a few CDC files have no topic and broken questions ("What is (are) ?")
            continue
        url = doc.get("url", "")
        # Ids are built from the file name and the pair's position in the file,
        # because some MedQuAD files reuse the same pid for several pairs.
        for q_no, qa in enumerate(doc.iter("QAPair"), 1):
            question_el = qa.find("Question")
            answer = clean(qa.findtext("Answer") or "")
            if question_el is None or len(answer.split()) < MIN_WORDS:
                continue
            question = " ".join((question_el.text or "").split())
            for n, passage in enumerate(split_passages(answer)):
                rows.append({
                    "id": f"{doc.get('source')}_{path.stem}_{q_no}_{n}",
                    "title": f"{focus}: {question}",
                    "text": passage,
                    "question": question,
                    "qtype": question_el.get("qtype", ""),
                    "topic": focus,
                    "source": SOURCES[folder.name],
                    "url": url,
                    "licence": LICENCE,
                })
    return rows


def main() -> None:
    if not RAW.exists():
        raise SystemExit(
            f"MedQuAD not found at {RAW}.\n"
            "Run: git clone https://github.com/abachaa/MedQuAD.git data/raw/medquad"
        )

    passages, seen, per_source = [], set(), Counter()
    duplicates = 0
    for name in SOURCES:
        for row in read_folder(RAW / name):
            key = hashlib.sha1(row["text"].lower().encode()).hexdigest()
            if key in seen:
                duplicates += 1
                continue
            seen.add(key)
            passages.append(row)
            per_source[row["source"]] += 1

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        for row in passages:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"Wrote {len(passages)} passages to {OUT.relative_to(ROOT)}")
    print(f"Dropped {duplicates} duplicate passages")
    for source, count in per_source.most_common():
        print(f"  {count:6d}  {source}")


if __name__ == "__main__":
    main()
