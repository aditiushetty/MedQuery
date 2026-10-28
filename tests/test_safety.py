"""Safety rule tests. Run from the project folder:  python -m pytest"""
import pytest

from app import safety


@pytest.mark.parametrize("question", [
    "I have chest pain and can't breathe",          # always urgent
    "My father collapsed and is unconscious",
    "I have chest pain",                            # happening now
    "my mother is having a seizure what do i do",
    "what to do if someone is having a stroke",
    "chest pain",                                   # unclear -> treated as urgent
    "I want to kill myself",
])
def test_emergencies(question):
    assert safety.check(question)[0] == "emergency"


@pytest.mark.parametrize("question", [
    "I am asking what might be the reason for chest pain",
    "what are the warning signs of a stroke",
    "symptoms of food poisoning",
    "how is epilepsy different from a seizure",
])
def test_questions_about_urgent_conditions_get_a_warning_not_a_block(question):
    assert safety.check(question)[0] == "warning"


def test_ordinary_question_is_not_urgent():
    assert safety.check("How is high blood pressure treated?") == (None, "")


def test_warning_note_gives_emergency_numbers():
    assert "112" in safety.warning_note("chest pain") and "108" in safety.warning_note("chest pain")
