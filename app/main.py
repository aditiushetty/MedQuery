"""MedQuery API (owner: Member 3).

Pipeline: safety check -> query understanding -> spelling correction ->
BM25 retrieval -> evidence check -> extractive answer with sources.
Run from the project folder:  uvicorn app.main:app --reload --port 8000
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import answer, nlu, research, retrieval, safety
from app.schemas import AskRequest, AskResponse, Entity, ResearchItem, Source

NO_EVIDENCE_MESSAGE = (
    "I could not find reliable information about this in my medical sources, "
    "so I can't give you an answer. Please ask a doctor or pharmacist."
)
CLARIFY_MESSAGE = (
    "Could you tell me which condition, symptom or treatment you mean? "
    'For example: "Is high blood pressure serious?"'
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    retrieval.warm_up()  # build the BM25 index at startup, not on the first question
    yield


app = FastAPI(title="MedQuery API", version="0.2.0", lifespan=lifespan)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest) -> AskResponse:
    # 1. Emergencies first: never wait on retrieval or show "low confidence".
    #    A question only ABOUT an urgent condition is answered, numbers first.
    urgency, phrase = safety.check(req.question)
    if urgency == "emergency":
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

    def reply(status, text, confidence=0.0, sources=(), studies=()) -> AskResponse:
        if urgency == "warning":
            text = safety.warning_note(phrase) + "\n\n" + text
        return AskResponse(
            status=status, answer=text, confidence=round(confidence, 2),
            intent=query["intent"], entities=entities, sources=list(sources),
            research=[ResearchItem(**s) for s in studies], disclaimer=safety.DISCLAIMER,
        )

    # 3. A question that names nothing ("Is it serious?") cannot be matched to evidence.
    if retrieval.is_generic(query["clean_query"]):
        return reply("low_confidence", CLARIFY_MESSAGE)

    # 4. Fix spelling. Words our sources never mention mean we have no evidence.
    words, unknown = retrieval.correct(query["clean_query"])
    # Terms only recognisable after spelling correction ("asthama" -> asthma).
    known = {e.mesh_id for e in entities}
    entities += [Entity(**e) for e in nlu.entities(" ".join(words)) if e["mesh_id"] not in known]
    # Add our sources' own names for those terms ("paracetamol" -> "acetaminophen").
    words, unknown = retrieval.expand_with_mesh(words, unknown, [e.model_dump() for e in entities])
    if unknown:
        return reply(
            "no_evidence",
            f"{NO_EVIDENCE_MESSAGE}\n\nMy sources don't mention: {', '.join(unknown)}.",
        )

    # 5. Find evidence and check it covers the question.
    #    Only a question about a condition we recognise can be "answered".
    passages = retrieval.search(" ".join(words), k=5, intent=query["intent"])
    best = max((p["coverage"] for p in passages), default=0.0)
    if retrieval.find_topic(words):
        status = "answered" if best >= answer.ANSWERED else "low_confidence"
        enough = best >= answer.LOW
    else:
        status = "low_confidence"
        enough = best >= answer.NO_TOPIC_LOW
    if not enough:
        return reply("no_evidence", NO_EVIDENCE_MESSAGE, best)

    # 6. Build the answer from the passages' own sentences.
    text, used = answer.build(words, passages)
    if not used:
        return reply("no_evidence", NO_EVIDENCE_MESSAGE, best)

    notes = []
    if words != retrieval.tokenize(query["clean_query"]):
        notes.append(f"_I searched for: {' '.join(words)}_")
    if status == "low_confidence":
        notes.append(answer.LOW_CONFIDENCE_NOTE)
    notes.append(text)
    if answer.PERSONAL.search(req.question):
        notes.append(answer.PERSONAL_NOTE)

    sources = [
        Source(id=p["id"], title=p["title"], source=p["source"], url=p["url"],
               snippet=p["text"], score=p["score"])
        for p in used
    ]
    # 7. Studies about the same conditions, shown separately as research.
    studies = research.related([e.model_dump() for e in entities])
    return reply(status, "\n\n".join(notes), best, sources, studies)
