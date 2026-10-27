# MedQuery

An intelligent medical question answering system using BERT and knowledge retrieval.
College mini-project. Educational prototype: it does not replace a qualified healthcare professional.

## Setup (once)

Python **3.11** is required (PyTorch and Transformers do not support newer versions yet).

macOS:

    python3.11 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt

Windows (PowerShell):

    py -3.11 -m venv .venv
    .venv\Scripts\Activate.ps1
    pip install -r requirements.txt

## Run

Two terminals, both in this folder with the venv active:

    uvicorn app.main:app --reload --port 8000
    streamlit run ui/app.py

API test page: http://127.0.0.1:8000/docs

## Test

    python -m pytest

## Status

✅ implemented and tested · 🟡 baseline or approximate · ⏳ planned

| Feature | Owner | Status |
|---|---|---|
| `/ask` API with agreed request/response format | Member 3 | ✅ |
| Chat interface with loading and error states | Member 4 | ✅ |
| Emergency keyword check (112 / 108) | Member 3 | ✅ (keyword rule, not triage) |
| No-evidence fallback and disclaimer | Member 3 | ✅ |
| Medical corpus (MedQuAD) | Member 1 | ⏳ |
| BM25 retrieval | Member 3 | ⏳ (stub returns nothing) |
| Semantic and hybrid retrieval | Member 3 | ⏳ |
| Intent classification (rules, then DistilBERT) | Member 2 | ⏳ (stub returns "general") |
| Answer built from retrieved sentences with sources | Member 3 | ⏳ |
| Test set and evaluation results | Member 1, Member 4 | ⏳ |

## Who owns what

| Member | Files |
|---|---|
| 1 Data | `scripts/prepare_corpus.py`, `data/`, test questions |
| 2 NLU | `app/nlu.py`, `training/intent/` |
| 3 Backend | `app/main.py`, `app/retrieval.py`, `app/safety.py`, `app/schemas.py` |
| 4 UI & testing | `ui/app.py`, `tests/`, `eval/` |

Change `app/schemas.py` only after the whole team agrees.

## Git routine

    git checkout main
    git pull
    git checkout -b feature/yourname-task
    # work on your own files
    git add <your files>
    git commit -m "What you did"
    git push -u origin feature/yourname-task

Then open a Pull Request on GitHub; a teammate reviews and merges it.
