# AI Essay Analyst (Streamlit Scaffold)

## Setup

1. **Clone the repository** and `cd` into it.
2. **Create & activate a virtual environment**.  You can do this manually:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
   or run the helper script:
   ```bash
   chmod +x setup_env.sh
   ./setup_env.sh
   ```
   The script will create `.venv/` if necessary, activate it, and install
   all required packages.  After running the script you can activate the
   environment later with `source .venv/bin/activate`.
3. **Install dependencies** (if not using the script):
   ```bash
   pip install -r requirements.txt
   ```
4. **Set your API key** – either `OPENAI_API_KEY` or `GEMINI_API_KEY` in a
   `.env` file at the repo root.  The code will copy `GEMINI_API_KEY` to
   `OPENAI_API_KEY` for compatibility but now emits a warning to avoid
   silently mutating the environment; prefer setting `OPENAI_API_KEY`.

   Example `.env`:
   ```dotenv
   GEMINI_API_KEY=ya29...your_key_here
   ```
5. **Launch the app**:
   ```bash
   streamlit run app.py
   ```

## Structure

- app.py: Streamlit UI
- analyst/: Backend logic modules
- data/corpus/: RAG reference docs
- .streamlit/config.toml: Theme config

This is a scaffold for further AI + RAG integration.

## Development & security

- Unit tests live under `tests/`; run them with `pytest` after installing
  the dependencies in `requirements.txt`.
- The app validates LLM outputs via `analyst/feedback_parser.py` to ensure
  only well-formed JSON is consumed.
- Environment key handling is centralised in `analyst/utils.py`.

Refer to `security_report.md` for a formal audit detailing vulnerabilities,
mitigations, and recommendations for production deployments.

### Input rules

- Essays must be at least 150 words and no more than 5 000 words; the UI
  prevents analysis otherwise and displays a warning.
- Uploaded text files should be UTF-8 encoded and under 1 MB in size.
- Whitespace‑only or empty submissions are rejected.

### PDF uploads

You can now upload PDF files in addition to `.txt` and `.md` files. The app attempts to extract text from PDFs using the `pypdf` library. If the PDF is a scanned image (contains no embedded text), OCR is required and the app will warn that it cannot extract text.

## Additional native dependencies

Several analysis features rely on external models and runtimes. To enable
all functionality, install the following after creating the venv:

```bash
/workspaces/EssayInsight/.venv/bin/python -m pip install -r requirements.txt
/workspaces/EssayInsight/.venv/bin/python -m spacy download en_core_web_sm
/workspaces/EssayInsight/.venv/bin/python -c "import nltk; nltk.download('punkt'); nltk.download('vader_lexicon')"
# LanguageTool (grammar) requires Java on the host system; install a JRE/JDK.
```

## CI snippet (example)

Add the following steps to your CI job before running tests to ensure models
are available and heavy deps are installed:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
python -c "import nltk; nltk.download('punkt'); nltk.download('vader_lexicon')"
# Note: LanguageTool requires Java; skip or mock grammar tests if Java isn't available in CI.
pytest -q
```
