"""Query understanding.

Entities: medical terms in the question, normalised to MeSH with the same
dictionary used to tag the knowledge base (app/mesh.py). This is a dictionary
baseline for entity recognition, not a trained model.

Intent: still a STUB ("general"). The next step replaces it with a rule-based
baseline, then a DistilBERT classifier. Keep the returned keys the same.
"""
from app import mesh


def entities(text: str) -> list[dict]:
    """MeSH concepts named in the text: {"text", "label", "mesh_id", "name"}."""
    return [
        {"text": f["text"], "label": f["branch"], "mesh_id": f["ui"], "name": f["name"]}
        for f in mesh.find(text)
    ]


def understand(question: str) -> dict:
    return {
        "clean_query": " ".join(question.lower().split()),
        "intent": "general",
        "intent_confidence": 0.0,
        "entities": entities(question),
    }
