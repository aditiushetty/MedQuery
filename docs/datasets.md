# Datasets

## MedQuAD (in use)

- What: 47,457 medical question-answer pairs from 12 NIH websites.
- Where: https://github.com/abachaa/MedQuAD (downloaded 2026-10-27 with `git clone --depth 1`).
- Licence: Creative Commons Attribution 4.0 (CC BY 4.0). We must credit it:
  Asma Ben Abacha and Dina Demner-Fushman. "A Question-Entailment Approach to Question Answering." BMC Bioinformatics, 2019.
- Patient data: none. These are public health information pages, not patient records.

### What we use

`scripts/prepare_corpus.py` turns 9 of the 12 folders into `data/processed/corpus.jsonl`:

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
| **Total** | **23,070** |

Processing: whitespace cleaned; answers longer than 200 words split into passages at paragraph or sentence ends; 3,374 exact duplicate passages dropped; 19 CDC passages without a topic dropped.

### What we do not use, and why

- **A.D.A.M. Medical Encyclopedia, MedlinePlus Drugs, MedlinePlus Herbs and Supplements:** MedQuAD removed their answers to respect MedlinePlus copyright. We do not scrape them back.
- **The LiveQA test zip:** not needed yet; could be used later for evaluation.

### Known limitations

- About 55% of passages are about rare genetic diseases (GHR, GARD). A common question can match a rare condition with a similar name (e.g. "diabetes" also matches "Brittle diabetes"). Retrieval must be tested for this.
- The data is from about 2017: no COVID-19, no recent drugs (e.g. semaglutide). Questions on these must get the no-evidence fallback.
- No drug-information pages, so medicine questions are poorly covered.
- The MedQuAD questions are templated ("What are the symptoms of X ?"). Our test questions are written in our own words so retrieval is not tested on near-copies.

## Planned, not downloaded

- **PubMedQA** (MIT licence): research abstracts; possible extra evidence and evaluation.
- **BioASQ**: requires registration; postponed.
