"""Check that the knowledge base files follow the agreed format.

Run from the project folder:  python scripts/validate_corpus.py
Exit code 0 = OK. Anything else = a file is broken; fix it before using it.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROCESSED = ROOT / "data" / "processed"

REQUIRED = ["id", "title", "text", "source", "url", "licence", "topic"]

# file -> (minimum passages, extra required fields)
FILES = {
    "corpus.jsonl": (2000, []),                                  # patient information (MedQuAD)
    "research.jsonl": (500, ["decision", "conclusion", "mesh_terms"]),  # PubMed abstracts (PubMedQA)
}


def check(path: Path, minimum: int, extra: list[str]) -> list[str]:
    if not path.exists():
        return [f"{path.name} not found; run its prepare script first"]
    problems, ids, count, words = [], set(), 0, 0
    with path.open(encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                problems.append(f"{path.name} line {line_no}: not valid JSON")
                continue
            count += 1
            missing = [k for k in REQUIRED + extra if not row.get(k)]
            if missing:
                problems.append(f"{path.name} line {line_no}: empty or missing {missing}")
            if not isinstance(row.get("mesh_ids"), list):  # may be empty, but must exist
                problems.append(f"{path.name} line {line_no}: no mesh_ids; run scripts/tag_mesh.py")
            if row.get("id") in ids:
                problems.append(f"{path.name} line {line_no}: duplicate id {row.get('id')}")
            ids.add(row.get("id"))
            words += len(str(row.get("text", "")).split())
    if count < minimum:
        problems.append(f"{path.name}: only {count} passages; need at least {minimum}")
    if not problems:
        print(f"OK: {path.name}: {count} passages, all fields present, ids unique, "
              f"average {words / count:.0f} words per passage")
    return problems


def main() -> int:
    problems = []
    mesh_file = PROCESSED / "mesh_terms.json"
    if mesh_file.exists():
        print(f"OK: mesh_terms.json: {len(json.loads(mesh_file.read_text())['terms'])} terms")
    else:
        problems.append("mesh_terms.json not found; run scripts/build_mesh.py")
    for name, (minimum, extra) in FILES.items():
        problems += check(PROCESSED / name, minimum, extra)
    for p in problems[:20]:
        print("FAIL:", p)
    if len(problems) > 20:
        print(f"... and {len(problems) - 20} more problems")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())