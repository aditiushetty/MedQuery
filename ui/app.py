"""MedQuery chat interface.

Start the backend first, then run from the project folder:  streamlit run ui/app.py
"""
import os

import requests
import streamlit as st

API_URL = os.environ.get("MEDQUERY_API", "http://127.0.0.1:8000")

STATUS_LABELS = {
    "answered": ("success", "Answer based on the sources below"),
    "low_confidence": ("warning", "Low confidence: the sources only partly match your question"),
    "no_evidence": ("warning", "No reliable evidence found"),
    "emergency": ("error", "Possible emergency"),
    "out_of_scope": ("info", "Outside what MedQuery can answer"),
}

st.set_page_config(page_title="MedQuery", page_icon="🩺")
st.title("🩺 MedQuery")
st.caption(
    "Educational prototype. General information only; "
    "not a substitute for a qualified healthcare professional."
)


DECISION_LABELS = {"yes": "Finding: yes", "no": "Finding: no", "maybe": "Finding: unclear"}


def show_reply(data: dict) -> None:
    kind, label = STATUS_LABELS.get(data["status"], ("info", data["status"]))
    getattr(st, kind)(label)
    if data.get("entities"):
        terms = " · ".join(
            f"`{e['text']}` → {e['name']} ({e['label']})" for e in data["entities"]
        )
        st.caption(f"Medical terms recognised (MeSH): {terms}")
    st.markdown(data["answer"])
    if data["sources"]:
        with st.expander(f"Sources ({len(data['sources'])})"):
            for i, s in enumerate(data["sources"], 1):
                st.markdown(f"**[{i}] {s['title']}** ({s['source']}, score {s['score']:.2f})")
                st.caption(s["snippet"])
                if s["url"]:
                    st.markdown(s["url"])
    if data.get("research"):
        with st.expander(f"Related research ({len(data['research'])} PubMed studies)"):
            st.caption(
                "Findings from studies of particular groups of people. "
                "They are research, not advice for you."
            )
            for r in data["research"]:
                st.markdown(f"**{r['question']}** ({r['year']})")
                st.markdown(f"{DECISION_LABELS.get(r['decision'], r['decision'])}. {r['conclusion']}")
                st.markdown(r["url"])
    st.caption(f"Intent: {data['intent']} · Confidence: {data['confidence']:.2f}")


if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg["role"] == "user":
            st.markdown(msg["content"])
        else:
            show_reply(msg["content"])

question = st.chat_input("Ask a general health question")
if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Searching medical sources..."):
            try:
                resp = requests.post(
                    f"{API_URL}/ask", json={"question": question, "history": []}, timeout=30
                )
                resp.raise_for_status()
                data = resp.json()
            except requests.ConnectionError:
                st.error(f"Can't reach the backend at {API_URL}. Is uvicorn running?")
                st.stop()
            except requests.RequestException as err:
                st.error(f"The backend returned an error: {err}")
                st.stop()
        show_reply(data)
    st.session_state.messages.append({"role": "assistant", "content": data})
