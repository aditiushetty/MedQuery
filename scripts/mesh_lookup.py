"""Show how MedQuery normalises a piece of text to MeSH, and how much of the
knowledge base is about each concept found.

Run from the project folder:
    python scripts/mesh_lookup.py "Can paracetamol help after a heart attack?"
"""
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import mesh  # noqa: E402

FILES = {"patient": ROOT / "data" / "processed" / "corpus.jsonl",
         "research": ROOT / "data" / "processed" / "research.jsonl"}


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit('Usage: python scripts/mesh_lookup.py "your question"')
    found = mesh.find(sys.argv[1])
    if not found:
        print("No MeSH concepts found in this text.")
        return

    counts = {name: Counter() for name in FILES}
    for name, path in FILES.items():
        for line in path.open(encoding="utf-8"):
            counts[name].update(json.loads(line).get("mesh_ids", []))

    for f in found:
        print(f"'{f['text']}' -> {f['ui']} {f['name']} ({f['branch']})")
        print(f"    passages: {counts['patient'][f['ui']]} patient, {counts['research'][f['ui']]} research")


if __name__ == "__main__":
    main()