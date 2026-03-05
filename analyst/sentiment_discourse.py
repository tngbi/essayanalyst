from __future__ import annotations

from typing import List, Tuple, Dict

_nlp = None
_sia = None


def _get_nlp():
    global _nlp
    if _nlp is None:
        try:
            import spacy

            _nlp = spacy.load("en_core_web_sm")
        except Exception:
            _nlp = None
    return _nlp


def _get_sia():
    global _sia
    if _sia is None:
        try:
            import nltk
            from nltk.sentiment import SentimentIntensityAnalyzer

            # Ensure required NLTK data is present; download quietly if not.
            for resource, download_id in [
                ("tokenizers/punkt", "punkt"),
                ("tokenizers/punkt_tab", "punkt_tab"),
                ("sentiment/vader_lexicon", "vader_lexicon"),
            ]:
                try:
                    nltk.data.find(resource)
                except LookupError:
                    nltk.download(download_id, quiet=True)

            _sia = SentimentIntensityAnalyzer()
        except Exception:
            _sia = None
    return _sia


def sentiment_analysis(text: str, top_n: int = 10) -> Tuple[List[Dict], List[Dict]]:
    nlp = _get_nlp()
    sia = _get_sia()
    if nlp is None:
        raise RuntimeError("spaCy model 'en_core_web_sm' not available. Run: python -m spacy download en_core_web_sm")
    if sia is None:
        raise RuntimeError("NLTK SentimentIntensityAnalyzer not available. Ensure NLTK and vader_lexicon are installed.")

    doc = nlp(text)
    sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]

    scored = []
    for s in sentences:
        score = sia.polarity_scores(s)["compound"]
        scored.append({"sentence": s, "score": score})

    positive = sorted(scored, key=lambda x: x["score"], reverse=True)[:top_n]
    negative = sorted(scored, key=lambda x: x["score"])[:top_n]
    return positive, negative


TRANSITION_WORDS = [
    "however","moreover","therefore","consequently",
    "furthermore","thus","in contrast","similarly",
    "nevertheless","accordingly",
]


def discourse_score(paragraph: str) -> float:
    import numpy as np

    sentences = [s for s in paragraph.split(".") if s.strip()]
    if len(sentences) < 2:
        return 1.0

    lengths = [len(s.split()) for s in sentences]
    avg_len = float(np.mean(lengths)) if lengths else 0.0
    transition_count = sum(1 for w in TRANSITION_WORDS if w in paragraph.lower())
    score = 1.5 + (transition_count * 0.2)
    if avg_len > 20:
        score += 0.3
    return round(score, 2)


def discourse_analysis(text: str, top_n: int = 10) -> Tuple[List[Dict], List[Dict]]:
    paragraphs = [p.strip() for p in text.split("\n") if len(p.strip()) > 50]
    scored = []
    for p in paragraphs:
        score = discourse_score(p)
        scored.append({"paragraph": p, "score": score})

    highest = sorted(scored, key=lambda x: x["score"], reverse=True)[:top_n]
    lowest = sorted(scored, key=lambda x: x["score"])[:top_n]
    return highest, lowest
