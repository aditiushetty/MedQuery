"""Retrieval tests (owner: Member 3). Run from the project folder:  python -m pytest"""
import pytest

from app import retrieval

if not retrieval.CORPUS.exists():
    pytest.skip("corpus not built; run scripts/prepare_corpus.py", allow_module_level=True)


def test_tokenize_drops_question_words_and_lemmatises():
    assert retrieval.tokenize("What are the symptoms of Asthma?") == ["symptom", "asthma"]


@pytest.mark.parametrize("typo, fixed", [
    ("symtoms", "symptom"), ("asthama", "asthma"), ("dibetes", "diabetes"),
    ("feaver", "fever"), ("pnemonia", "pneumonia"), ("hypertenshun", "hypertension"),
    ("infraction", "infarction"),   # rare medical word, very close spelling
])
def test_spelling_is_corrected_to_common_corpus_words(typo, fixed):
    assert retrieval.correct(typo) == ([fixed], [])


@pytest.mark.parametrize("word", ["covid", "semaglutide", "cricket", "engine"])
def test_unknown_words_are_not_turned_into_other_diseases(word):
    words, unknown = retrieval.correct(word)
    assert unknown == [word]


def test_topic_is_the_most_specific_condition_named():
    assert retrieval.find_topic(["warning", "signs", "diabetes"]) == "diabetes"
    assert retrieval.find_topic(["high", "blood", "pressure", "treated"]) == "high blood pressure"
    assert retrieval.find_topic(["fever", "rash", "measles"]) == "measles"
    assert retrieval.find_topic(["capital", "france"]) is None


def test_search_stays_on_the_named_condition():
    results = retrieval.search("warning signs diabetes")
    assert results
    assert all(p["topic"].lower() == "diabetes" for p in results)


def test_search_prefers_the_question_type_from_the_intent():
    results = retrieval.search("asthma", intent="treatment")
    assert results[0]["qtype"] == "treatment"


def test_coverage_is_between_0_and_1():
    for p in retrieval.search("high blood pressure treatment"):
        assert 0.0 <= p["coverage"] <= 1.0
