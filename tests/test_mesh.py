"""MeSH normalisation tests. Run from the project folder:  python -m pytest"""
import pytest

from app import mesh

if not mesh.DICTIONARY.exists():
    pytest.skip("MeSH dictionary not built; run scripts/build_mesh.py", allow_module_level=True)


def names(text: str) -> list[str]:
    return [f["name"] for f in mesh.find(text)]


@pytest.mark.parametrize("text, concept", [
    ("heart attack", "Myocardial Infarction"),         # MeSH synonym
    ("high blood pressure", "Hypertension"),           # longest phrase wins over "pressure"
    ("paracetamol", "Acetaminophen"),                  # drug name variant
    ("diabetes", "Diabetes Mellitus"),                 # from our lay_terms.csv
    ("loose motions", "Diarrhea"),                     # Indian English, lay_terms.csv
    ("anaemia", "Anemia"),                             # British spelling, lay_terms.csv
    ("COVID-19", "COVID-19"),
    ("covid", "COVID-19"),
])
def test_text_is_normalised_to_mesh(text, concept):
    assert names(text) == [concept]


def test_several_concepts_in_order_each_once():
    assert names("Can paracetamol help after a heart attack? Is paracetamol safe?") == [
        "Acetaminophen", "Myocardial Infarction"]


def test_everyday_words_are_not_tagged():
    assert names("this will lead to cold water and all aids recovery") == []


def test_short_acronyms_match_only_in_capitals():
    assert names("Symptoms of AIDS") == ["Acquired Immunodeficiency Syndrome"]
    assert names("rest aids recovery") == []


def test_general_concepts_are_ignored():
    assert names("signs and symptoms and treatments") == []