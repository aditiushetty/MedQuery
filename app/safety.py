"""Safety rules that run before anything else.

This is a simple keyword check, not a medical triage system. It is deliberately
cautious: "what is a heart attack?" also triggers it. That is a known limitation
we accept, because missing a real emergency is worse than an extra warning.
"""

DISCLAIMER = (
    "MedQuery is an educational prototype. It gives general information from public "
    "medical sources and does not replace a qualified healthcare professional."
)

# Emergency numbers for India: 112 (all emergencies), 108 (ambulance).
EMERGENCY_MESSAGE = (
    "This sounds like it could be urgent. Please call 112 or 108 (ambulance) now, "
    "or go to the nearest emergency department. MedQuery cannot help in an emergency."
)

EMERGENCY_PHRASES = [
    "chest pain",
    "heart attack",
    "can't breathe",
    "cannot breathe",
    "difficulty breathing",
    "trouble breathing",
    "stroke",
    "unconscious",
    "fainted",
    "seizure",
    "severe bleeding",
    "bleeding heavily",
    "overdose",
    "poisoning",
    "swallowed poison",
    "suicide",
    "kill myself",
    "end my life",
    "self harm",
]


def is_emergency(question: str) -> bool:
    text = question.lower().replace("’", "'").replace("-", " ")
    return any(phrase in text for phrase in EMERGENCY_PHRASES)
