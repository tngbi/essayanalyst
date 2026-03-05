# Copilot instructions — EssayInsight

Quick guidance to help AI coding agents be immediately productive in this repository.

## Big picture
- Entrypoint: [app.py](app.py) (Streamlit UI). The app calls `analyst.analyse_essay()` and expects a JSON-shaped analysis to populate the UI.
- Core backend: the `analyst/` package implements the scoring and retrieval pipeline:
  - [analyst/scorer.py](analyst/scorer.py) — orchestrates RAG, constructs prompts, calls the LLM, and parses JSON output.
  - [analyst/prompts.py](analyst/prompts.py) — authoritative system prompt and user prompt builder; it defines the exact JSON schema the frontend expects.
  - [analyst/rag_retriever.py](analyst/rag_retriever.py) — builds/loads a FAISS index from `data/corpus/` and returns retrieved context + sources.
  - [analyst/feedback_parser.py](analyst/feedback_parser.py) — placeholder for parsing/validation of raw LLM responses (currently `pass`).

## Key patterns & constraints
- Strict JSON contract: `analyst/prompts.py`'s `SYSTEM_PROMPT` requires the LLM to return a fixed JSON shape (scores, band, strengths, weaknesses, revision_roadmap, confidence, confidence_notes). Do not change keys without updating `app.py` which reads those keys directly.
- RAG index and corpus: source documents live under [data/corpus](data/corpus). Index files are written to `data/faiss_index` by `analyst/rag_retriever.build_or_load_index()`; code assumes a FAISS index may already exist and will load it if present.
- Minimal parser present: `analyst/feedback_parser.py` is unimplemented; the pipeline currently trusts the LLM and directly json.loads() the response in `scorer.py`.

## Developer workflows & commands
- Run locally (dev): create a virtualenv, `pip install -r requirements.txt`, add `OPENAI_API_KEY` to a `.env` file, then:

  ```bash
  streamlit run app.py
  ```

- To rebuild the RAG index (uses your OpenAI embedding credentials): run a short script or import & call `analyst.rag_retriever.build_or_load_index()` from a small runner. The index is created at `data/faiss_index`.

## Project-specific conventions
- System prompt is authoritative: keep the JSON schema stable. Example fields shown in [analyst/prompts.py](analyst/prompts.py).
- `analyse_essay()` returns a dict with `scores`, `band`, `strengths`, `weaknesses`, `revision_roadmap`, `confidence`, and `rag_sources` — `app.py` expects these exact shapes when rendering tabs.
- Small utilities and parsing should live under `analyst/` (e.g., `feedback_parser.py` for response validation).

## Integration points & dependencies
- LLM provider: `analyst/scorer.py` uses the `openai` client; API key read from `OPENAI_API_KEY` via `python-dotenv`.
- Embeddings/vectorstore: `analyst/rag_retriever.py` uses `OpenAIEmbeddings` and FAISS (`langchain_community` wrappers). Ensure `faiss-cpu` and the matching LangChain packages are installed (see `requirements.txt`).

## When editing code, watch for these gotchas
- Do not change the JSON schema in `SYSTEM_PROMPT` without updating `app.py` and `prompts.py` together.
- `analyst/scorer.py` currently uses `json.loads()` on the LLM output — add robust validation in `analyst/feedback_parser.py` if you modify LLM prompts or the response format.
- RAG pipeline silently returns `None` if no docs are available; `app.py` expects an empty `rag_sources` list in that case.

## Short checklist for PRs that touch analysis or RAG
- Update `analyst/prompts.py` if you change scoring dimensions.
- Add/complete parsing in `analyst/feedback_parser.py` when changing LLM outputs.
- Run `streamlit run app.py` manually to check UI rendering of scores.

If any section is unclear or you want more examples (unit tests, a small runner to rebuild the FAISS index, or stricter validation helpers), tell me which piece to expand.
