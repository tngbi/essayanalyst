import sys, os
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from analyst import rag_retriever


from analyst.utils import ensure_api_key


def test_env_copy_for_rag():
    os.environ.pop("OPENAI_API_KEY", None)
    os.environ["GEMINI_API_KEY"] = "abc"
    ensure_api_key()
    assert os.getenv("OPENAI_API_KEY") == "abc"
