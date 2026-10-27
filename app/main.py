"""MedQuery API (owner: Member 3).

Pipeline: safety check -> query understanding -> retrieval -> answer.
Run from the project folder:  uvicorn app.main:app --reload --port 8000
"""
from fastapi import FastAPI

from app import nlu, retrieval, safety
from app.schemas import AskRequest, AskResponse, Entity, Source

NO_EVIDENCE_MESSAGE = (
    "I could not find reliable information about this in my medical sources, "
    "so I can't give you an answer. Please ask a doctor or pharmacist."
)

app = FastAPI(title="MedQuery API", version="0.1.0")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest) -> AskResponse:
    # 1. Emergencies first: never wait on retrieval or show "low confidence".
    if safety.is_emergency(req.question):
        return AskResponse(
            status="emergency",
            answer=safety.EMERGENCY_MESSAGE,
            confidence=0.0,
            intent="emergency",
            disclaimer=safety.DISCLAIMER,
        )

    # 2. Understand the question.
    query = nlu.understand(req.question)
    entities = [Entity(**e) for e in query["entities"]]

    # 3. Find evidence.
    passages = retrieval.search(query["clean_query"], k=5)
    if not passages:
        return AskResponse(
            status="no_evidence",
            answer=NO_EVIDENCE_MESSAGE,
            confidence=0.0,
            intent=query["intent"],
            entities=entities,
            disclaimer=safety.DISCLAIMER,
        )

    # 4. Build the answer. Milestone 3 replaces this placeholder with
    #    sentences extracted from the passages.
    sources = [
        Source(
            id=p["id"], title=p["title"], source=p["source"], url=p["url"],
            snippet=p["text"][:300], score=p["score"],
        )
        for p in passages
    ]
    return AskResponse(
        status="low_confidence",
        answer="(Answer builder not implemented yet. See the sources below.)",
        confidence=0.0,
        intent=query["intent"],
        entities=entities,
        sources=sources,
        disclaimer=safety.DISCLAIMER,
    )
