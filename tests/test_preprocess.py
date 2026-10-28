"""Preprocessing tests. Run from the project folder:  python -m pytest"""
import pytest

from app import preprocess


@pytest.mark.parametrize("word, expected", [
    ("symptoms", "symptom"),    # plural noun
    ("treated", "treat"),       # past tense verb
    ("treating", "treat"),
    ("children", "child"),      # irregular plural
    ("women", "woman"),
    ("diagnosed", "diagnose"),
    ("diabetes", "diabetes"),   # medical names WordNet keeps as they are
    ("measles", "measles"),
])
def test_lemma(word, expected):
    assert preprocess.lemma(word) == expected


def test_tokenize_lowercases_drops_stopwords_and_lemmatises():
    assert preprocess.tokenize("How are Children with Asthma treated?") == ["child", "asthma", "treat"]


def test_question_and_passage_wording_now_match():
    # Different word forms in the question and the passage become the same tokens.
    assert set(preprocess.tokenize("treating seizures")) == set(preprocess.tokenize("seizure treated"))