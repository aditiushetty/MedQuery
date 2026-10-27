"""Medical passage retrieval (owner: Member 3).

STUB for Milestone 1. It finds nothing, so every question takes the
"no_evidence" path. Member 3 replaces it with BM25 over
data/processed/corpus.jsonl, then adds semantic search.
"""


def search(query: str, k: int = 5) -> list[dict]:
    """Return up to k passages, best first.

    Each passage: {"id", "title", "source", "url", "text", "score"}
    """
    return []
