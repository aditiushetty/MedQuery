"""Tag every knowledge base passage with the MeSH concepts it mentions.

Input/output: data/processed/corpus.jsonl and data/processed/research.jsonl
              (each passage gets a new field "mesh_ids": a list of MeSH ids)
Needs:        data/processed/mesh_terms.json (scripts/build_mesh.py)

Run from the project folder:  python scripts/tag_mesh.py

Run it again whenever you rebuild a corpus file, because the prepare scripts
write the files without tags.
"""
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import mesh  # noqa: E402

FILES = [ROOT / "data" / "processed" / "corpus.jsonl", ROOT / "data" / "processed" / "research.jsonl"]


def tag_file(path: Path, counts: Counter) -> None:
    rows = [json.loads(line) for line in path.open(encoding="utf-8")]
    untagged = 0
    for row in rows:
        found = mesh.find(row["title"] + ". " + row["text"])
        row["mesh_ids"] = [f["ui"] for f in found]
        counts.update(f["ui"] for f in found)
        untagged += not found
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    tags = sum(len(r["mesh_ids"]) for r in rows)
    print(f"{path.name}: {len(rows)} passages, {tags / len(rows):.1f} MeSH concepts per passage, "
          f"{untagged} with none")


def main() -> None:
    counts: Counter = Counter()
    for path in FILES:
        if not path.exists():
            raise SystemExit(f"{path.name} not found; run its prepare script first")
        tag_file(path, counts)

    concepts = mesh._load()["concepts"]
    print(f"\n{len(counts)} different MeSH concepts found. Most frequent (check these make sense):")
    for ui, n in counts.most_common(25):
        print(f"  {n:6d}  {ui:12s} {concepts[ui]['name']} ({concepts[ui]['branch']})")


if __name__ == "__main__":
    main()