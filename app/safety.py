"""Safety rules that run before anything else.

This is a keyword check, not a medical triage system. It sorts a question into:

  "emergency"  someone seems to be in danger now: show only the emergency message
  "warning"    a question ABOUT an urgent condition ("what causes chest pain?"):
               answer it, but put the emergency numbers first
  None         nothing urgent mentioned

Rules, in order:
1. Phrases that always mean danger now ("can't breathe", "unconscious",
   "kill myself") -> emergency.
2. Urgent conditions ("chest pain", "stroke", "seizure") -> emergency when the
   question says it is happening ("I have", "my father is having", "right now"),
   warning when it only asks for information ("what", "why", "symptoms of"),
   and emergency when neither is clear. When unsure we treat it as urgent,
   because missing a real emergency is worse than an extra warning.

Known limits: it reads words, not meaning. "My chest pain from last year" is
treated as happening now; unusual wording of a real emergency can be missed.
"""
import re

DISCLAIMER = (
    "MedQuery is an educational prototype. It gives general information from public "
    "medical sources and does not replace a qualified healthcare professional."
)

# Emergency numbers for India: 112 (all emergencies), 108 (ambulance).
EMERGENCY_MESSAGE = (
    "This sounds like it could be urgent. Please call 112 or 108 (ambulance) now, "
    "or go to the nearest emergency department. MedQuery cannot help in an emergency."
)

ALWAYS_URGENT = [
    "can't breathe", "cannot breathe", "cant breathe", "not breathing",
    "unconscious", "fainted", "collapsed", "severe bleeding", "bleeding heavily",
    "overdose", "swallowed poison", "suicide", "kill myself", "end my life", "self harm",
]

URGENT_CONDITIONS = [
    "chest pain", "heart attack", "difficulty breathing", "trouble breathing",
    "stroke", "seizure", "poisoning",
]

# Signs that it is happening to someone now.
HAPPENING = re.compile(
    r"\b(i|i'm|im|we|he|she|they|someone|somebody|my \w+)\s+"
    r"(have|has|had|having|am having|is having|are having|got|feel|feels|just had)\b"
    r"|\b(right now|now|suddenly|currently|at the moment|help me|what should i do|what do i do)\b"
)

# Signs that it is a request for information.
ASKING = re.compile(
    r"\b(what|why|how|which|when|reason|reasons|cause|causes|symptoms?|signs?|"
    r"tests?|diagnos\w*|prevent\w*|treat\w*|risk|risks|difference|mean|means)\b"
)

WARNING_NOTE = (
    "**Is this happening to you or someone near you right now? Call 112 or 108 "
    "(ambulance) immediately.** The information below about {condition} is general, "
    "not emergency advice."
)


def _normalise(question: str) -> str:
    return question.lower().replace("’", "'").replace("-", " ")


def check(question: str) -> tuple[str | None, str]:
    """Return ("emergency" | "warning" | None, the urgent phrase found)."""
    text = _normalise(question)
    for phrase in ALWAYS_URGENT:
        if phrase in text:
            return "emergency", phrase
    for phrase in URGENT_CONDITIONS:
        if phrase in text:
            if HAPPENING.search(text) or not ASKING.search(text):
                return "emergency", phrase
            return "warning", phrase
    return None, ""


def is_emergency(question: str) -> bool:
    return check(question)[0] == "emergency"


def warning_note(phrase: str) -> str:
    return WARNING_NOTE.format(condition=phrase)
