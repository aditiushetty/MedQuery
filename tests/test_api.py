"""API tests. Run from the project folder:  python -m pytest

These use the real corpus, so build it first (scripts/prepare_corpus.py).
"""
import re

import pytest
from fastapi.testclient import TestClient

from app import retrieval
from app.main import app

if not retrieval.CORPUS.exists():
    pytest.skip("corpus not built; run scripts/prepare_corpus.py", allow_module_level=True)

client = TestClient(app)


def ask(question: str) -> dict:
    r = client.post("/ask", json={"question": question})
    assert r.status_code == 200
    return r.json()


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_emergency_question_gets_emergency_status():
    body = ask("I have chest pain and can't breathe")
    assert body["status"] == "emergency"
    assert "112" in body["answer"]
    assert body["sources"] == []


def test_question_about_something_not_in_sources_falls_back():
    body = ask("Is semaglutide good for weight loss?")
    assert body["status"] == "no_evidence"
    assert body["sources"] == []
    assert "semaglutide" in body["answer"]
    assert body["disclaimer"]


def test_question_that_names_nothing_asks_for_detail():
    body = ask("Is it serious?")
    assert body["status"] == "low_confidence"
    assert body["sources"] == []


def test_empty_question_is_rejected():
    assert client.post("/ask", json={"question": ""}).status_code == 422


def test_normal_question_is_answered_with_sources():
    body = ask("How is high blood pressure treated?")
    assert body["status"] == "answered"
    assert body["sources"]
    assert all(s["title"].startswith("High Blood Pressure") for s in body["sources"])


@pytest.mark.parametrize("question", [
    "How is high blood pressure treated?",
    "What are the warning signs of diabetes?",
    "symtoms of asthama",
    "I have a fever and a rash. Do I have measles?",
])
def test_every_answer_sentence_is_copied_from_its_cited_source(question):
    """The grounding check: each bullet ends in [n], and its text must appear
    word for word in source n. This is what "evidence-grounded" means here."""
    body = ask(question)
    bullets = [line for line in body["answer"].splitlines() if line.startswith("- ")]
    assert bullets
    for line in bullets:
        m = re.fullmatch(r"- (.+) \[(\d+)\]", line)
        assert m, f"bullet without a citation: {line}"
        sentence, n = m.group(1), int(m.group(2))
        assert 1 <= n <= len(body["sources"]), f"citation [{n}] points to no source"
        assert sentence in body["sources"][n - 1]["snippet"]


def test_us_emergency_number_is_never_shown():
    for q in ["What are the warning signs of diabetes?", "What are the symptoms of a stroke?"]:
        assert "911" not in ask(q)["answer"]


def test_personal_diagnosis_question_gets_no_diagnosis():
    body = ask("I have a fever and a rash. Do I have measles?")
    assert "can't tell whether this applies to you" in body["answer"]
    assert "you have measles" not in body["answer"].lower()


def test_medical_terms_are_recognised_and_returned():
    body = ask("How is high blood pressure treated?")
    assert [(e["text"], e["name"], e["mesh_id"]) for e in body["entities"]] == [
        ("high blood pressure", "Hypertension", "D006973")]


@pytest.mark.parametrize("question, topic", [
    ("what is myocardial infarction", "Heart Attack"),   # MeSH synonym of our topic name
    ("I have loose motions and fever", "Diarrhea"),      # Indian English, from lay_terms.csv
])
def test_mesh_synonyms_find_the_corpus_topic(question, topic):
    body = ask(question)
    assert body["status"] == "answered"
    assert body["sources"][0]["title"].startswith(topic)


def test_concept_missing_from_sources_still_gets_no_evidence():
    body = ask("Is the COVID-19 booster safe for older people?")
    assert body["status"] == "no_evidence"
    assert body["entities"][0]["name"] == "COVID-19"   # recognised, but we have no passages


def test_related_research_is_about_the_condition_and_labelled():
    body = ask("symtoms of asthama")
    assert body["research"]
    for study in body["research"]:
        assert study["decision"] in {"yes", "no", "maybe"}
        assert study["url"].startswith("https://pubmed.ncbi.nlm.nih.gov/")


def test_no_research_without_a_recognised_condition():
    assert ask("Is it serious?")["research"] == []


def test_question_about_chest_pain_is_answered_with_emergency_numbers_first():
    body = ask("I am asking what might be the reason for chest pain")
    assert body["status"] != "emergency"
    assert body["answer"].startswith("**Is this happening")
    assert "112" in body["answer"] and body["sources"]


def test_misspelled_medical_term_is_corrected_and_normalised():
    body = ask("what is myocardial infraction")      # typo of "infarction"
    assert body["entities"][0]["name"] == "Myocardial Infarction"
    assert body["sources"][0]["title"].startswith("Heart Attack")
