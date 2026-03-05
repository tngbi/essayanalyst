import json, os
from dotenv import load_dotenv
from analyst.prompts import SYSTEM_PROMPT, build_user_prompt
from analyst.rag_retriever import retrieve_context
from analyst.feedback_parser import parse_feedback

load_dotenv()

from analyst.utils import ensure_api_key

# make sure we honour either environment variable
ensure_api_key()

_client = None

def _get_client():
    global _client
    if _client is None:
        from openai import OpenAI
        _client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _client

def analyse_essay(essay: str, level: str, discipline: str,
                  rubric: str, use_rag: bool, max_refs: int = 7) -> dict:

    rag_context, sources = "", []
    if use_rag:
        rag_context, sources = retrieve_context(essay[:2000], k=max_refs)

    user_prompt = build_user_prompt(essay, level, discipline, rubric, rag_context)

    try:
        # Use the chat completions endpoint without the `response_format`
        # kwarg for broad compatibility with the installed OpenAI client.
        # The LLM is instructed (see prompts) to return a JSON string which
        # we validate with `parse_feedback` below.
        response = _get_client().chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_prompt},
            ],
            temperature=0.2,
        )
    except Exception as exc:
        # could be network error, API quota, etc.
        raise RuntimeError("failed to contact LLM service") from exc

    raw = response.choices[0].message.content
    try:
        result = parse_feedback(raw)
    except ValueError as exc:
        # wrap in runtime error so callers can handle generically
        raise RuntimeError("unexpected response format from LLM") from exc

    result["rag_sources"] = sources
    return result
