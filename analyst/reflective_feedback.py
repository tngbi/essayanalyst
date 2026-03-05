from __future__ import annotations

import os
from typing import Optional


SYSTEM_PROMPT = """
You are an academic reflective writing evaluator.

Evaluate the reflective piece using Driscoll's model:

1. WHAT – description of the experience or topic
2. SO WHAT – interpretation, implications, learning
3. NOW WHAT – future actions, improvements, applications

Provide structured feedback covering:

• Context and implications
• Plan of action
• Critical feedback
• Summary
• Next steps

Return the response in structured paragraphs.
"""


def _get_client():
    from openai import OpenAI
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY is not set in the environment")
    return OpenAI(api_key=key)


def reflective_llm_feedback(text: str, model: str = "gpt-4o-mini", temperature: float = 0.3) -> str:
    """Send the reflective piece to the LLM and return structured feedback as text.

    Raises RuntimeError if the API key is missing or the LLM call fails.
    """
    client = _get_client()

    prompt = f"""
Reflective Piece:

{text}

Analyse the reflection using Driscoll's model:

WHAT?
SO WHAT?
NOW WHAT?

Provide academic feedback.
"""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
        )
    except Exception as exc:
        raise RuntimeError("LLM request failed") from exc

    # Defensive: extract text from response structure
    try:
        return response.choices[0].message.content
    except Exception:
        raise RuntimeError("Unexpected LLM response format")
