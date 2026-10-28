# MedQuery

An intelligent medical question answering system using BERT and knowledge retrieval.
College mini-project. Educational prototype: it does not replace a qualified healthcare professional.

## Setup (once)

Python **3.11** is required (PyTorch and Transformers do not support newer versions yet).

macOS:

    python3.11 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    python -m nltk.downloader wordnet

Windows (PowerShell):

    py -3.11 -m venv .venv
    .venv\Scripts\Activate.ps1
    pip install -r requirements.txt
    python -m nltk.downloader wordnet

## Build the knowledge base (once)

Download the three sources (about 20 MB in total):

    git clone --depth 1 https://github.com/abachaa/MedQuAD.git data/raw/medquad
    curl -L --create-dirs -o data/raw/pubmedqa/ori_pqal.json https://raw.githubusercontent.com/pubmedqa/pubmedqa/master/data/ori_pqal.json
    curl -L --create-dirs -o data/raw/mesh/desc2026.gz https://nlmpubs.nlm.nih.gov/projects/mesh/MESH_FILES/xmlmesh/desc2026.gz

Then build and validate everything (about 10 seconds):

    python scripts/build_kb.py

The built files are not stored in Git. What is in the knowledge base, where it
comes from, its licences and limitations: `docs/datasets.md`.

Try the MeSH normalisation: `python scripts/mesh_lookup.py "Can paracetamol help after a heart attack?"`

## Run

Two terminals, both in this folder with the venv active:

    uvicorn app.main:app --reload --port 8000
    streamlit run ui/app.py

API test page: http://127.0.0.1:8000/docs

## Test

    python -m pytest
    python eval/run_eval.py

## Status

✅ implemented and tested · 🟡 baseline or approximate · ⏳ planned

| Feature | Status |
|---|---|
| Knowledge base: MedQuAD patient passages (23,070) | ✅ |
| Knowledge base: PubMedQA research abstracts (1,000) | ✅ stored; ⏳ not yet used in answers |
| MeSH entity normalisation (18,952 concepts, every passage tagged) | ✅ stored; ⏳ not yet used in search |
| Preprocessing: tokenisation, stopwords, WordNet lemmatisation | ✅ |
| One-command build and validation (`scripts/build_kb.py`) | ✅ |
| `/ask` API with request/response format | ✅ |
| Chat interface with loading and error states | ✅ |
| Emergency keyword check (112 / 108) | ✅ (keyword rule, not triage) |
| No-evidence fallback and disclaimer | ✅ |
| BM25 retrieval, with spelling correction and condition (topic) recognition | ✅ |
| Extractive answer: copied sentences with [n] citations, checked by a test | ✅ |
| Evidence check: coverage score and thresholds -> answered / low confidence / no evidence | 🟡 (word matching, tuned on 31 questions) |
| Semantic and hybrid retrieval | ⏳ |
| Intent classification (rules, then DistilBERT) | ⏳ (stub returns "general") |
| Test set | 🟡 (14 of 40 questions) |
| Evaluation script (`eval/run_eval.py`) | ✅ |
| Evaluation on held-out questions | ⏳ |

## Project layout

| Folder | What is in it |
|---|---|
| `app/` | API (`main.py`), preprocessing, retrieval, answers, MeSH matcher, safety rules |
| `ui/` | Streamlit chat page |
| `scripts/` | Knowledge base build, validation and lookup scripts |
| `data/` | Raw downloads and built files (not in Git), `lay_terms.csv`, `test_questions.csv` |
| `tests/` | Automated tests (`python -m pytest`) |
| `eval/` | Evaluation script and saved results |
| `docs/` | Knowledge base documentation, evidence screenshots |

## Git routine

    git checkout main
    git pull
    git checkout -b feature/short-name
    # make the change, run the tests
    git add .
    git commit -m "What you did"
    git push -u origin feature/short-name

Then open a Pull Request on GitHub and merge it.