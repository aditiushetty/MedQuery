# MedQuery knowledge base

Everything MedQuery knows comes from the files described here. It writes no
medical facts of its own: answers are sentences copied from these sources, with
citations.

## Summary

| Part | File (built, not in Git) | Size | Used for |
|---|---|---|---|
| Patient information (MedQuAD) | `data/processed/corpus.jsonl` | 23,070 passages, 2.98 million words, 4,739 topics | Answers to patients |
| Research evidence (PubMedQA) | `data/processed/research.jsonl` | 1,000 PubMed abstracts, 240,867 words, 1989-2017 | "Related research" under answers |
| Medical vocabulary (MeSH 2026) | `data/processed/mesh_terms.json` | 18,952 concepts, 115,342 terms, 427 acronyms | Entity normalisation (tags on every passage) |
| Everyday terms (ours) | `data/lay_terms.csv` (in Git) | 22 terms | Words MeSH lacks: "flu", "piles", "loose motions" |

Rebuild everything with one command (about 10 seconds):

    python scripts/build_kb.py

## How it is built

    MedQuAD XML ──> prepare_corpus.py ──> corpus.jsonl ──┐
    PubMedQA JSON ─> prepare_pubmedqa.py > research.jsonl ┼─> tag_mesh.py ──> validate_corpus.py
    MeSH XML + lay_terms.csv ─> build_mesh.py ─> mesh_terms.json ┘   (adds mesh_ids)

At search time, `app/preprocess.py` turns every passage and every question into
the same kind of word list (see Preprocessing).

## Sources

### MedQuAD (patient information)
- **What:** 47,457 medical question-answer pairs from 12 NIH websites (cancer.gov, NIDDK, NHLBI, NINDS, CDC, MedlinePlus, GARD, Genetics Home Reference, NIHSeniorHealth).
- **Where:** https://github.com/abachaa/MedQuAD (downloaded 2026-10-27).
- **Licence:** CC BY 4.0. Citation: Asma Ben Abacha and Dina Demner-Fushman, "A Question-Entailment Approach to Question Answering", BMC Bioinformatics, 2019.
- **Processing:** 9 of 12 folders used; answers cleaned, split into passages of at most 200 words at paragraph or sentence ends; 3,374 exact duplicates and 19 passages without a topic dropped.

| Source | Passages |
|---|---|
| Genetics Home Reference (NLM) | 6,365 |
| Genetic and Rare Diseases Information Center (GARD) | 6,330 |
| National Cancer Institute | 2,484 |
| NIDDK | 2,148 |
| NHLBI | 1,597 |
| NIHSeniorHealth | 1,430 |
| NINDS | 1,228 |
| MedlinePlus Health Topics | 1,063 |
| CDC | 425 |

Each passage keeps MedQuAD's question type, used to match the kind of question
asked: information 6,162, treatment 4,208, symptoms 3,763, genetic changes 1,633,
exams and tests 1,435, frequency 1,119, inheritance 1,111, causes 1,044,
susceptibility 532, prevention 425, others 1,638.

### PubMedQA (research evidence, PubMed abstracts)
- **What:** 1,000 expert-labelled research questions. Each has a PubMed abstract, the MeSH terms PubMed gave the article, the abstract's conclusion and an expert yes / no / maybe answer (552 / 338 / 110).
- **Where:** https://github.com/pubmedqa/pubmedqa, file `data/ori_pqal.json` (downloaded 2026-10-28).
- **Licence:** MIT (the dataset). The abstract text belongs to its publishers; we use it for education and do not publish it (the file is not in Git).
- **Citation:** Qiao Jin, Bhuwan Dhingra, Zhengping Liu, William Cohen and Xinghua Lu, "PubMedQA: A Dataset for Biomedical Research Question Answering", EMNLP 2019.
- **Why separate:** abstracts are written for researchers, so they are never quoted to patients as plain advice. Each passage is marked `"collection": "research"`.

### MeSH 2026 (medical vocabulary)
- **What:** Medical Subject Headings, the U.S. National Library of Medicine's controlled vocabulary used to index PubMed. Each concept has an id, a preferred name and its other names (e.g. D009203 Myocardial Infarction = "heart attack").
- **Where:** https://nlmpubs.nlm.nih.gov/projects/mesh/MESH_FILES/xmlmesh/desc2026.gz (downloaded 2026-10-28).
- **Licence:** free to use; courtesy of the U.S. National Library of Medicine.
- **Kept:** diseases (5,064 concepts), mental disorders (125), drugs and chemicals (10,685), procedures (3,078).
- **Filtered out:** 54 everyday words that are also MeSH terms ("lead", "cold", "water"), 19 concepts too general to identify a subject ("Signs and Symptoms", "Therapeutics", "Methods"), and short acronyms in lower case ("aids" is not AIDS). Found by tagging the corpus and reading the most frequent matches.

## Excluded sources

| Source (named in our synopsis) | Decision | Reason |
|---|---|---|
| **MIMIC-III** clinical notes | Not used | Requires credentialed PhysioNet access (ethics course and application review, days to weeks). It contains real hospital patient records, which conflicts with our privacy design, and doctors' notes about individual patients are not patient-friendly answers. Replaced by MedQuAD. |
| **BioASQ** | Not used yet | Requires registration. A possible future addition. |
| MedQuAD's A.D.A.M., MedlinePlus Drugs and Herbs folders | Not used | MedQuAD's authors removed these answers for copyright; we do not scrape them back. |

## Preprocessing

The same steps run on every passage and every question (`app/preprocess.py`):

| Step | Example | How |
|---|---|---|
| Tokenisation | "How are children treated?" -> how, are, children, treated | regular expression |
| Lower case and stopword removal | -> children, treated | fixed list of 101 words |
| Lemmatisation | -> child, treat | NLTK WordNet lemmatiser (noun form, else verb form) |
| Spelling correction (questions only) | "symtoms of asthama" -> symptom, asthma | closest common corpus word with the same first letter |
| MeSH normalisation | "heart attack" -> D009203 Myocardial Infarction | longest dictionary match, `app/mesh.py` |

**Lemmatisation versus stemming:** stemming cuts word endings and can produce
non-words ("diabetes" -> "diabet"); lemmatisation returns dictionary words, which
keeps spelling correction and the "I searched for" line readable.

**Measured effect of lemmatisation** (31 questions: 14 test questions and 17 tuning questions, run with and without it):

| | Without | With |
|---|---|---|
| Expected status | 27/31 | 27/31 |
| Right topic in top 5 | 21/21 | 21/21 |
| Right question type in top 5 | 10/17 | 10/17 |

Better: "can children get migraines" now finds Migraine (plural matched), and
topics that differ only in form ("Kidney Disease", "Kidney Diseases") are merged.
Worse: "can dogs eat chocolate" moved from no evidence to low confidence, and the
typo "sings" (for "signs") is now read as the real word "sing" and not corrected.
On this small set the overall effect is neutral; we keep it because it is part
of our method and handles word forms consistently.

## Passage format

Patient passage (`corpus.jsonl`):

    {"id": "NHLBI_0000010_1_1", "title": "Asthma: What is (are) Asthma ?", "text": "...",
     "question": "What is (are) Asthma ?", "qtype": "information", "topic": "Asthma",
     "source": "NHLBI (nhlbi.nih.gov)", "url": "https://...", "licence": "CC BY 4.0 (...)",
     "mesh_ids": ["D001249", ...]}

Research passage (`research.jsonl`) adds `conclusion`, `decision` (yes/no/maybe),
`year`, `mesh_terms` (PubMed's own) and `"collection": "research"`.

## MeSH tagging results

| | Patient | Research |
|---|---|---|
| Concepts per passage (average) | 5.6 | 6.2 |
| Passages with no concept | 989 (4%) | 9 (1%) |
| Different concepts found | 5,625 | 1,947 |

Most frequent: Neoplasms, Drug Therapy, Infections, Genetic Testing, Seizures,
Diabetes Mellitus, Hypertension, Stroke, Fever, Anemia.

## Known limitations

- About 55% of patient passages are about rare genetic diseases (GHR, GARD); common questions can match a rare condition with a similar name.
- The data is from about 2017 or earlier: no COVID-19, no newer drugs. Such questions get the no-evidence answer.
- No drug-information pages (removed for copyright), so medicine questions are poorly covered.
- MeSH matching is a dictionary lookup: it does not understand negation ("no fever") and misses words not in MeSH or our lay list.
- Related research is matched by MeSH concept only: a study is shown because it is about the same condition, not because it answers the question.