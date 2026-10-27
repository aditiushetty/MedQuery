"""API tests. Run from the project folder:  python -m pytest"""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_emergency_question_gets_emergency_status():
    r = client.post("/ask", json={"question": "I have chest pain and can't breathe"})
    assert r.status_code == 200
    assert r.json()["status"] == "emergency"
    assert "112" in r.json()["answer"]


def test_unknown_question_falls_back_without_inventing_an_answer():
    r = client.post("/ask", json={"question": "What causes migraines?"})
    body = r.json()
    assert body["status"] == "no_evidence"
    assert body["sources"] == []
    assert body["disclaimer"]


def test_empty_question_is_rejected():
    assert client.post("/ask", json={"question": ""}).status_code == 422
