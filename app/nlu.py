"""Query understanding (owner: Member 2).

STUB for Milestone 1. It only cleans the text. Member 2 replaces the body of
understand() with a rule-based intent baseline, then a DistilBERT classifier.
Keep the function name and the returned keys exactly the same.
"""


def understand(question: str) -> dict:
    return {
        "clean_query": " ".join(question.lower().split()),
        "intent": "general",
        "intent_confidence": 0.0,
        "entities": [],  # list of {"text": str, "label": str}
    }
