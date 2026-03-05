# Security Assessment — AI Essay Analyst

This document summarises the major security (and robustness) issues identified
during a formal audit of the application, along with recommended mitigations.

> **Scope:** repository files under `/workspaces/EssayInsight`; local Python
> environment running on Linux.  The application is a Streamlit frontend
> backed by an LLM + RAG pipeline using OpenAI/Gemini.

---

## 1. Model output validation

**Issue:** `analyst.scorer.analyse_essay()` previously performed
`json.loads()` on the raw LLM response without validation.  A malformed or
malicious response could lead to exceptions, incorrect UI rendering or even
code injection if the data were executed later.

**Impact:** crash of the app, untrusted data used downstream, denial of service
or data corruption.

**Mitigation:** we now validate responses with `pydantic` models in
`analyst/feedback_parser.py`.  The parser raises a `ValueError` on any schema
violation; `scorer.analyse_essay()` catches this and surfaces a runtime error
that the UI can display gracefully.  All tests cover valid/invalid inputs.

## 2. Prompt‑injection / user‑controlled content

**Issue:** essays are interpolated directly into the chat prompt.  A user
could craft text containing LLM instructions which may influence the model in
unintended ways.

**Impact:** model could ignore scoring rubric, leak sensitive data, or
perform arbitrary actions.

**Mitigation:** (future work) sanitise or escape essay text; send essay in a
separate `assistant` message or as a chunked document using the OpenAI
`input` parameter rather than raw prompt text.  Log untrusted content for
monitoring.

## 3. Environment variable handling

**Issue:** key-copy code was duplicated between modules; lacking a central
helper made it hard to test and could lead to inconsistent behaviour.

**Mitigation:** added `analyst/utils.ensure_api_key()` with unit tests.  This
helper is idempotent and runs early in both `scorer` and `rag_retriever`.

## 4. Dependency risks & supply chain

- Dependencies were loosely specified (`langchain>=0.1.12`) and upgraded to
  incompatible versions during development, causing import errors.
- `allow_dangerous_deserialization=True` is used when loading FAISS index; if
  the index is ever built from untrusted data it could execute arbitrary
  code.

**Mitigation:** pinned `langchain==0.1.12` and added `pytest` & `pydantic` to
requirements.  Documentation now emphasises rebuilding the index (`scripts/`)
and warns about unsafe deserialization.  Consider switching to a safer
serialization format or verifying the index file's integrity before loading.

## 5. Untrusted file handling

- File uploader in UI accepts arbitrary `.txt`/`.md` content which is
  decoded without size checks; large files could degrade memory.
- `PyPDFLoader` processes PDF files from `data/corpus` only, but those
  documents could theoretically contain malicious payloads.

**Mitigation:** limit upload size, warn users in UI, and restrict corpus
maintenance to trusted operators. In a deployed environment run the app in a
container with resource quotas.

## 6. Lack of error handling for external services

**Issue:** network errors, API rate limits, or missing API keys simply raised
exceptions that bubbled to the top.

**Mitigation:** `analyse_essay()` now catches exceptions from the OpenAI
client and rethrows a `RuntimeError` with a generic message.  The app should
use `st.error(...)` when rendering such exceptions (not yet implemented).
Further enhancements: retry logic, circuit breakers, request throttling.

## 7. UI-related concerns

- The 150‑word check can be trivially bypassed with whitespace; data must be
  validated server‑side before calling the LLM.
- Session state stores history in memory; adversaries could manipulate it via
  crafted essays or cookies.

**Mitigation:** reinforce server-side checks (already does because `analyse_essay`
requires essay text) and consider clearing history on session expiry.

## 8. Secrets & configuration

The app uses `.env` for API keys.  If the repository were accidentally pushed to
VCS with a real key, it could be compromised.

**Mitigation:** update `.gitignore` to exclude `.env` (already typical) and
use environment‑specific secret managers for production.  Rotate keys
regularly.

## 9. Recommendations for deployment

1. Restrict access (authentication & rate limiting). 2. Run inside a sandboxed,
   resource‑limited container. 3. Monitor requests and logs for anomalous
   prompts or repeated failures. 4. Periodically rebuild and re-index the
   corpus in a trusted environment. 5. Add security headers to the Streamlit
   server or proxy it behind a secure web server.

---

### Conclusion
The application is a simple but flexible RAG‑powered essay evaluator.  The
changes made during this audit—schema validation, helper extraction, lazy
imports, dependency pinning and a test suite—significantly improve its
robustness.  However, any service that invokes an LLM on user content should
be treated as untrusted and deployed with appropriate security controls
outlined above.

Please review and integrate these recommendations as part of your
deployment or further development process.