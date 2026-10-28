"""Build a MeSH dictionary: every way of writing a medical term -> its standard MeSH concept.

Input:  data/raw/mesh/desc2026.gz
        (download: https://nlmpubs.nlm.nih.gov/projects/mesh/MESH_FILES/xmlmesh/desc2026.gz)
        data/lay_terms.csv  (our own list of everyday words MeSH lacks, e.g. "flu", "piles")
Output: data/processed/mesh_terms.json

Run from the project folder:  python scripts/build_mesh.py

MeSH (Medical Subject Headings) is the US National Library of Medicine's
controlled vocabulary. Each concept ("descriptor") has an id, a preferred name
and many entry terms, e.g. D009203 "Myocardial Infarction" is also written
"Heart Attack". PubMed indexes every article with MeSH, so mapping our text and
the user's question onto MeSH ids is what "entity normalisation" means here.

We keep 4 branches of the MeSH tree (the letter its tree numbers start with):
  C   Diseases                      F03 Mental disorders
  D   Drugs and chemicals           E   Diagnosis, therapy and other procedures
"""
import csv
import gzip
import json
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw" / "mesh" / "desc2026.gz"
LAY_TERMS = ROOT / "data" / "lay_terms.csv"
OUT = ROOT / "data" / "processed" / "mesh_terms.json"

BRANCHES = {"C": "disease", "F03": "mental disorder", "D": "drug or chemical", "E": "procedure"}

# Entry terms that are also everyday English words, so matching them would tag
# ordinary text ("lead to", "cold water"). Found by tagging the corpus and
# reading the most frequent matches (scripts/tag_mesh.py prints them).
IGNORE = {
    "lead", "cold", "can", "map", "set", "acid", "salt", "water", "oxygen",
    "light", "sun", "air", "iron", "milk", "sugar", "gas", "glass", "sleep", "rest",
    "tissue", "food", "foods", "diet", "drug", "drugs", "fat", "fats",
    "protein", "proteins", "therapy", "therapeutics", "treatment", "surgery",
    "diagnosis", "disease", "diseases", "syndrome", "disorder", "disorders",
    "pain", "risk", "methods", "method", "test", "tests", "growth", "weight",
    "exercise", "pressure", "stress", "age", "help", "range", "nursing",
}


# Concepts too general to say what a passage is about. Each is triggered by
# everyday wording ("signs and symptoms", "treatments", "procedure", "measure").
# Found from the frequency list scripts/tag_mesh.py prints.
IGNORE_CONCEPTS = {
    "Signs and Symptoms", "Therapeutics", "Rare Diseases", "Diagnosis", "Methods",
    "Prognosis", "Aftercare", "Risk Factors", "Weights and Measures", "Needles",
    "Coloring Agents", "Registries", "Diagnostic Tests, Routine", "Disease",
    "Syndrome", "Pathologic Processes", "Pharmaceutical Preparations",
    "Prevalence", "Incidence",
}


def branch_of(tree_numbers: list[str]) -> str | None:
    for tree in tree_numbers:
        for prefix, label in BRANCHES.items():
            if tree.startswith(prefix):
                return label
    return None


def main() -> None:
    if not RAW.exists():
        raise SystemExit(
            f"MeSH not found at {RAW}.\nDownload it with:\n"
            "curl -L --create-dirs -o data/raw/mesh/desc2026.gz "
            "https://nlmpubs.nlm.nih.gov/projects/mesh/MESH_FILES/xmlmesh/desc2026.gz"
        )

    concepts, terms, acronyms = {}, {}, {}
    ambiguous, per_branch = set(), Counter()

    # iterparse reads one record at a time, so the 300 MB file never sits in memory.
    with gzip.open(RAW, "rb") as f:
        for _, record in ET.iterparse(f):
            if record.tag != "DescriptorRecord":
                continue
            ui = record.findtext("DescriptorUI")
            name = record.findtext("DescriptorName/String")
            trees = [t.text for t in record.iterfind("TreeNumberList/TreeNumber")]
            strings = {t.text for t in record.iterfind("ConceptList/Concept/TermList/Term/String")}
            record.clear()

            branch = branch_of(trees)
            if not branch or name in IGNORE_CONCEPTS:
                continue
            concepts[ui] = {"name": name, "branch": branch}
            per_branch[branch] += 1

            for s in strings | {name}:
                # Skip inverted forms ("Infarction, Myocardial"): the normal word order is also listed.
                if not s or ", " in s or len(s) < 3:
                    continue
                if s.isupper() and " " not in s and len(s) < 5:
                    acronyms.setdefault(s, ui)  # "AIDS", "COPD": matched only in capitals
                    continue                    # (longer ones like "COVID-19" match any case)
                key = s.lower()
                if key in IGNORE:
                    continue
                if key in terms and terms[key] != ui:
                    ambiguous.add(key)
                terms.setdefault(key, ui)

    for key in ambiguous:  # a term that means two different concepts tells us nothing
        terms.pop(key, None)

    # Our own everyday terms. Each must name a real MeSH concept, or we stop.
    by_name = {c["name"]: ui for ui, c in concepts.items()}
    lay = 0
    with LAY_TERMS.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            ui = by_name.get(row["mesh_name"])
            if not ui:
                raise SystemExit(f"lay_terms.csv: '{row['mesh_name']}' is not a MeSH name we kept")
            terms[row["term"].lower()] = ui
            lay += 1

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "source": "MeSH 2026, U.S. National Library of Medicine",
        "concepts": concepts,
        "terms": terms,
        "acronyms": acronyms,
    }, ensure_ascii=False), encoding="utf-8")

    print(f"Kept {len(concepts)} MeSH concepts: {dict(per_branch)}")
    print(f"Wrote {len(terms)} terms and {len(acronyms)} acronyms to {OUT.relative_to(ROOT)}")
    print(f"Dropped {len(ambiguous)} terms that mean more than one concept")
    print(f"Added {lay} everyday terms from {LAY_TERMS.relative_to(ROOT)}")


if __name__ == "__main__":
    main()