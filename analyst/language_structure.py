from __future__ import annotations

from typing import Dict
import collections

# Heavy/optional dependencies are imported lazily so tests and minimal
# environments can import this module without them installed.
_nlp = None


def _get_nlp():
    global _nlp
    if _nlp is None:
        try:
            import spacy
            _nlp = spacy.load("en_core_web_sm")
        except Exception:
            _nlp = None
    return _nlp


TRANSITION_WORDS = [
    "accordingly","afterward","also","besides","consequently","conversely",
    "finally","furthermore","however","in contrast","indeed","instead",
    "likewise","meanwhile","moreover","nevertheless","otherwise",
    "similarly","therefore","thus",
]

FUNCTION_POS = ["DET","ADP","PRON","CCONJ","SCONJ","PART","AUX"]
CONTENT_POS = ["NOUN","VERB","ADJ","ADV"]


def vocabulary_analysis(text: str) -> Dict[str, float]:
    nlp = _get_nlp()
    if nlp is None:
        raise RuntimeError("spaCy model 'en_core_web_sm' not available. Run: python -m spacy download en_core_web_sm")

    doc = nlp(text)
    tokens = [t.text.lower() for t in doc if t.is_alpha]
    total_words = max(1, len(tokens))

    nouns = set([t.text.lower() for t in doc if t.pos_ == "NOUN"])
    functions = set([t.text.lower() for t in doc if t.pos_ in FUNCTION_POS])
    content = set([t.text.lower() for t in doc if t.pos_ in CONTENT_POS])
    transitions = [t for t in tokens if t in TRANSITION_WORDS]

    results = {
        "unique_noun_pct": round(len(nouns) / total_words * 100, 2),
        "unique_function_pct": round(len(functions) / total_words * 100, 2),
        "unique_content_pct": round(len(content) / total_words * 100, 2),
        "unique_transition_pct": round(len(transitions) / total_words * 100, 2),
    }

    return results


def readability_score(text: str) -> float:
    try:
        import textstat
        score = textstat.flesch_reading_ease(text)
    except Exception:
        score = 0.0
    return round(float(score), 2)


ZONE_KEYWORDS = {
    "Objective":["aim","objective","this essay aims","this study aims"],
    "Method":["method","approach","framework","analysis uses","we apply"],
    "Result":["result","finding","demonstrates","shows that"],
    "Conclusion":["in conclusion","to conclude","overall","in summary"],
    "Background":["generally","in recent years","traditionally","commonly"],
    "Related-work":["previous research","studies show","literature suggests"],
    "Future-work":["future work","further research","future research"],
    "Review":["however","in contrast","critically","although"],
}


def classify_sentence(sentence: str) -> str:
    s = sentence.lower()
    for zone, words in ZONE_KEYWORDS.items():
        for w in words:
            if w in s:
                return zone
    return "Background"


def argumentative_zoning(text: str) -> Dict[str, float]:
    nlp = _get_nlp()
    if nlp is None:
        raise RuntimeError("spaCy model 'en_core_web_sm' not available. Run: python -m spacy download en_core_web_sm")

    doc = nlp(text)
    sentences = [sent.text for sent in doc.sents]
    zones = [classify_sentence(s) for s in sentences]
    counts = collections.Counter(zones)
    total = max(1, len(sentences))

    results = {}
    for z in ZONE_KEYWORDS.keys():
        results[z] = round(counts.get(z, 0) / total * 100, 2)

    return results


def zoning_chart(zones: Dict[str, float]):
    import plotly.express as px  # lazy import
    labels = list(zones.keys())
    values = list(zones.values())
    fig = px.pie(values=values, names=labels, title="Argumentative Zoning")
    return fig
