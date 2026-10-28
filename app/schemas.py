"""Shared request/response shapes for MedQuery.

Every member codes against these. Change them only after the whole team agrees,
because the backend, the UI and the tests all depend on them.
"""
from typing import Literal

from pydantic import BaseModel, Field

# What happened to a question:
#   answered        - good evidence was found and an answer was built from it
#   low_confidence  - some evidence was found, but it is weak
#   no_evidence     - nothing useful in our corpus
#   emergency       - the question sounds urgent; we point to emergency help
#   out_of_scope    - not a general medical question
Status = Literal["answered", "low_confidence", "no_evidence", "emergency", "out_of_scope"]


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)
    history: list[dict] = []  # earlier turns; used later for follow-up questions


class Entity(BaseModel):
    text: str          # as written in the question, e.g. "heart attack"
    label: str         # MeSH branch: disease, mental disorder, drug or chemical, procedure
    mesh_id: str = ""  # e.g. "D009203"
    name: str = ""     # MeSH preferred name, e.g. "Myocardial Infarction"


class ResearchItem(BaseModel):
    """A PubMed study about a condition in the question. Shown as research,
    never as advice: its finding comes from one study population."""
    id: str
    question: str    # the study's research question
    decision: str    # expert yes / no / maybe answer to that question
    conclusion: str  # the abstract's own conclusion
    year: str
    url: str


class Source(BaseModel):
    id: str       # corpus passage id, e.g. "medquad_0001"
    title: str
    source: str   # e.g. "MedQuAD (NIDDK)"
    url: str
    snippet: str  # the passage text we used
    score: float  # retrieval score (higher = more relevant)


class AskResponse(BaseModel):
    status: Status
    answer: str
    confidence: float  # 0..1; how well the evidence matches the question, NOT medical correctness
    intent: str
    entities: list[Entity] = []
    sources: list[Source] = []
    research: list[ResearchItem] = []
    disclaimer: str
