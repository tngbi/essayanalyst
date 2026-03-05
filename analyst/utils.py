"""Utility helpers shared across analyst modules."""

import os
import warnings


def ensure_api_key():
    """Copy GEMINI_API_KEY to OPENAI_API_KEY if the latter is missing.

    This allows the codebase to accept either environment variable but
    ensures that the libraries we call (which expect OPENAI_API_KEY) always
    see a value.  It's idempotent and safe to call multiple times.
    """
    if not os.getenv("OPENAI_API_KEY") and os.getenv("GEMINI_API_KEY"):
        warnings.warn(
            "GEMINI_API_KEY is set — copying to OPENAI_API_KEY for compatibility. "
            "Consider setting OPENAI_API_KEY explicitly.",
            UserWarning,
        )
        os.environ["OPENAI_API_KEY"] = os.getenv("GEMINI_API_KEY")
