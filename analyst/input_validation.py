"""Utility routines for checking essay text before analysis."""
from typing import Tuple


def count_words(text: str) -> int:
    """Return a simple word count (splitting on whitespace)."""
    if not text:
        return 0
    return len(text.split())


def validate_essay(
    text: str,
    min_words: int = 150,
    max_words: int = 5000,
    max_upload_bytes: int = 1_000_000,
) -> Tuple[bool, str]:
    """Perform a series of sanity checks on submitted essay text.

    Returns (is_valid, message).  The message is empty when valid; otherwise
    it contains a human-readable reason for rejection.
    """
    if not text or not text.strip():
        return False, "Essay is empty or contains only whitespace."

    wc = count_words(text)
    if wc < min_words:
        return False, f"Please enter at least {min_words} words (you have {wc})."
    if wc > max_words:
        return False, f"Essay exceeds maximum word limit of {max_words}."

    # note: file size check is for uploaded files, not plain text; caller should
    # perform that separately if needed.

    return True, ""
