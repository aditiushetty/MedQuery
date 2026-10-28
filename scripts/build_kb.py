"""Build the whole knowledge base with one command, in the right order.

Run from the project folder:  python scripts/build_kb.py

Needs the raw downloads in data/raw/ (see README "Build the knowledge base").
Stops at the first step that fails.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

STEPS = [
    ("Patient passages (MedQuAD)", "scripts/prepare_corpus.py"),
    ("Research abstracts (PubMedQA)", "scripts/prepare_pubmedqa.py"),
    ("MeSH dictionary", "scripts/build_mesh.py"),
    ("MeSH tags on every passage", "scripts/tag_mesh.py"),
    ("Validation", "scripts/validate_corpus.py"),
]


def main() -> None:
    for n, (label, script) in enumerate(STEPS, 1):
        print(f"\n=== Step {n}/{len(STEPS)}: {label} ===", flush=True)
        if subprocess.run([sys.executable, str(ROOT / script)], cwd=ROOT).returncode != 0:
            raise SystemExit(f"\nStopped: {script} failed. Fix the error above and run again.")
    print("\nKnowledge base built and validated.")


if __name__ == "__main__":
    main()