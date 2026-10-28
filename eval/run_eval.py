"""Run the test set through MedQuery and record the results (owner: Member 4).

Run from the project folder:
    python eval/run_eval.py                 # writes eval/results/latest.csv
    python eval/run_eval.py --name m3_bm25  # writes eval/results/m3_bm25.csv

Two kinds of checks per question:
- Behaviour: did /ask return the expected status (answered, no_evidence, ...)?
- Retrieval (only for questions with an expected topic): is a passage about that
  topic among the top 5 retrieved, and is one of the expected question type?
These are measured, not judged by hand. Whether the answer TEXT is good still
needs a person to read it: see the "answer" column.
"""
import argparse
import csv
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient  # noqa: E402

from app import nlu, retrieval  # noqa: E402
from app.main import app  # noqa: E402

TESTS = ROOT / "data" / "test_questions.csv"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", default="latest")
    args = parser.parse_args()

    rows = list(csv.DictReader(TESTS.open(encoding="utf-8")))
    results = []
    with TestClient(app) as client:
        for row in rows:
            start = time.perf_counter()
            body = client.post("/ask", json={"question": row["question"]}).json()
            ms = (time.perf_counter() - start) * 1000

            topic_hit = qtype_hit = ""
            if row["expected_topic"]:
                words, _ = retrieval.correct(nlu.understand(row["question"])["clean_query"])
                top5 = retrieval.search(" ".join(words), k=5)
                expected = set(retrieval.tokenize(row["expected_topic"]))
                topic_hit = any(set(retrieval.tokenize(p["topic"])) == expected for p in top5)
                wanted = set(filter(None, row["expected_qtype"].split(";")))
                qtype_hit = any(p["qtype"] in wanted for p in top5) if wanted else ""

            results.append({
                "id": row["id"],
                "category": row["category"],
                "question": row["question"],
                "expected_status": row["expected_status"],
                "status": body["status"],
                "status_ok": body["status"] == row["expected_status"],
                "topic_in_top5": topic_hit,
                "qtype_in_top5": qtype_hit,
                "confidence": body["confidence"],
                "n_sources": len(body["sources"]),
                "ms": round(ms),
                "answer": body["answer"].replace("\n", " "),
            })

    out = ROOT / "eval" / "results" / f"{args.name}.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0]))
        writer.writeheader()
        writer.writerows(results)

    def share(values) -> str:
        values = [v for v in values if v != ""]
        return f"{sum(values)}/{len(values)}" if values else "n/a"

    print(f"Questions:                {len(results)}")
    print(f"Expected status:          {share([r['status_ok'] for r in results])}")
    print(f"Right topic in top 5:     {share([r['topic_in_top5'] for r in results])}")
    print(f"Right question type in 5: {share([r['qtype_in_top5'] for r in results])}")
    print(f"Slowest answer:           {max(r['ms'] for r in results)} ms")
    for r in results:
        if not r["status_ok"]:
            print(f"  MISS {r['id']}: expected {r['expected_status']}, got {r['status']}  ({r['question']})")
    print(f"Saved to {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
