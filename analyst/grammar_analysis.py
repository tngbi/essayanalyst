from __future__ import annotations

from typing import List, Dict

_tool = None
_nlp = None


def _get_tool():
    global _tool
    if _tool is None:
        try:
            import language_tool_python

            _tool = language_tool_python.LanguageTool("en-GB")
        except Exception:
            _tool = None
    return _tool


def _get_nlp():
    global _nlp
    if _nlp is None:
        try:
            import spacy

            _nlp = spacy.load("en_core_web_sm")
        except Exception:
            _nlp = None
    return _nlp


def grammar_suggestions(text: str) -> List[Dict[str, object]]:
    """Return grammar/spelling suggestions using LanguageTool.

    Raises RuntimeError if LanguageTool is not available.
    """
    tool = _get_tool()
    if tool is None:
        raise RuntimeError(
            "language_tool_python is not available. Install it and ensure JVM is present."
        )

    matches = tool.check(text)
    suggestions = []
    for m in matches:
        start = max(0, m.offset - 40)
        end = min(len(text), m.offset + m.error_length + 40)
        context = text[start:end]
        suggestions.append({
            "text": context,
            "message": m.message,
            "replacements": m.replacements[:3],
        })

    return suggestions


def long_sentences(text: str, threshold: int = 64) -> List[Dict[str, object]]:
    """Return sentences longer than `threshold` words. Raises RuntimeError if spaCy model missing."""
    nlp = _get_nlp()
    if nlp is None:
        raise RuntimeError(
            "spaCy model 'en_core_web_sm' not available. Run: python -m spacy download en_core_web_sm"
        )

    doc = nlp(text)
    results = []
    for sent in doc.sents:
        words = [w for w in sent.text.split() if w.strip()]
        if len(words) > threshold:
            results.append({"sentence": sent.text, "length": len(words)})

    return results
