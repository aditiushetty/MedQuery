"""Check that data/processed/corpus.jsonl follows the agreed format (owner: Member 1).

Run from the project folder:  python scripts/validate_corpus.py
Exit code 0 = OK. Anything else = the corpus is broken; fix it before others use it.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "data" / "processed" / "corpus.jsonl"

REQUIRED = ["id", "title", "text", "source", "url", "licence", "topic"]
MIN_PASSAGES = 2000


def main() -> int:
    if not CORPUS.exists():
        print(f"FAIL: {CORPUS.relative_to(ROOT)} not found. Run scripts/prepare_corpus.py first.")
        return 1

    problems, ids, count, words = [], set(), 0, 0
    with CORPUS.open(encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                problems.append(f"line {line_no}: not valid JSON")
                continue
            count += 1
            missing = [k for k in REQUIRED if not str(row.get(k, "")).strip()]
            if missing:
                problems.append(f"line {line_no}: empty or missing {missing}")
            if row.get("id") in ids:
                problems.append(f"line {line_no}: duplicate id {row.get('id')}")
            ids.add(row.get("id"))
            words += len(str(row.get("text", "")).split())

    if count < MIN_PASSAGES:
        problems.append(f"only {count} passages; need at least {MIN_PASSAGES}")

    for p in problems[:20]:
        print("FAIL:", p)
    if len(problems) > 20:
        print(f"... and {len(problems) - 20} more problems")
    if problems:
        return 1
    print(f"OK: {count} passages, all fields present, ids unique, "
          f"average {words / count:.0f} words per passage")
    return 0


if __name__ == "__main__":
    sys.exit(main())
