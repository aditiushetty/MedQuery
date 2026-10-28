"""Text preprocessing shared by the knowledge base and the questions.

The same steps run on every passage (when the search index is built) and on
every question, so both sides end up as the same kind of word list:

1. Tokenisation      "Is she being treated?"  -> is, she, being, treated
2. Lower case and stopword removal                 -> treated
3. Lemmatisation (WordNet)                         -> treat

Lemmatisation turns each word into its dictionary form, so "treated",
"treating" and "treats" all become "treat", and "symptoms" becomes "symptom".
We use NLTK's WordNet lemmatiser: it looks words up in the WordNet dictionary
(no model, no training). Medical names it does not know, like "diabetes" or
"measles", are left as they are. Stemming (cutting word endings) was the other
option; we chose lemmatisation because it always gives real words, which keeps
the spelling correction and the answers readable.

Set LEMMATIZE = False to compare search results without it.
"""
import re
from functools import lru_cache

LEMMATIZE = True

# Words that carry no medical meaning. Question words go too: every MedQuAD
# title starts with "What is" or "What are", so they would match everything.
STOPWORDS = set("""
a an the and or of to in on for with without by from at as is are was were be been being
do does did can could should would will may might must shall i me my we our you your he she
it its they them their this that these those there here what which who whom whose when where
why how if then than so not no yes about into over under again also just only very too more
most some any all each both few other such own same s t get got have has had having
""".split())


@lru_cache(maxsize=1)
def _lemmatizer():
    try:
        from nltk.corpus import wordnet
        from nltk.stem import WordNetLemmatizer
        wordnet.ensure_loaded()
    except LookupError:
        raise RuntimeError(
            "The WordNet dictionary is missing. Download it once with:\n"
            "    python -m nltk.downloader wordnet"
        ) from None
    return WordNetLemmatizer()


@lru_cache(maxsize=200_000)
def lemma(word: str) -> str:
    """Dictionary form of a lower-case word: as a noun first ("symptoms" ->
    "symptom"), else as a verb ("treated" -> "treat")."""
    lemmatizer = _lemmatizer()
    noun = lemmatizer.lemmatize(word, "n")
    return noun if noun != word else lemmatizer.lemmatize(word, "v")


def tokenize(text: str) -> list[str]:
    words = [w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOPWORDS and len(w) > 1]
    return [lemma(w) for w in words] if LEMMATIZE else words