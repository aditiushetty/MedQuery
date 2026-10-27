"""Look up passages by word, to fill in expected source ids for the test set (owner: Member 1).

Run from the project folder:
    python scripts/find_passages.py migraine
    python scripts/find_passages.py "high blood pressure" --qtype symptoms

Matches the words against the passage topic and title (not the full text), so
you see the passages that are ABOUT the topic.
"""
import argparse
import json
from pathlib import Path

CORPUS = Path(__file__).resolve().parent.parent / "data" / "processed" / "corpus.jsonl"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("words", help="topic words, e.g. migraine")
    parser.add_argument("--qtype", help="e.g. symptoms, treatment, prevention, causes")
    parser.add_argument("--limit", type=int, default=15)
    args = parser.parse_args()

    needle = args.words.lower()
    shown = 0
    with CORPUS.open(encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            if needle not in (row["topic"] + " " + row["title"]).lower():
                continue
            if args.qtype and row.get("qtype") != args.qtype:
                continue
            print(f"{row['id']:40s} [{row.get('qtype', '')}] {row['title']}")
            print(f"{'':40s} {row['source']}: {row['text'][:110]}...")
            shown += 1
            if shown >= args.limit:
                break
    if not shown:
        print(f"No passages about '{args.words}'. Questions on this topic should get the no-evidence fallback.")


if __name__ == "__main__":
    main()
