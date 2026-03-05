import sys, os
import json
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from analyst import scorer
from analyst.scorer import analyse_essay

class DummyChoice:
    def __init__(self, content):
        class Msg:
            def __init__(self, content):
                self.content = content
        self.message = Msg(content)

class DummyResponse:
    def __init__(self, content):
        self.choices = [DummyChoice(content)]


class DummyCompletions:
    def __init__(self, fn):
        self._fn = fn
    def create(self, *args, **kwargs):
        return self._fn(*args, **kwargs)

class DummyChat:
    def __init__(self, fn):
        self.completions = DummyCompletions(fn)

class DummyClient:
    def __init__(self, fn):
        self.chat = DummyChat(fn)


from analyst.utils import ensure_api_key


def test_env_key_copy():
    # ensure GEMINI_API_KEY is copied when OPENAI_API_KEY missing
    os.environ.pop("OPENAI_API_KEY", None)
    os.environ["GEMINI_API_KEY"] = "gemini-value"
    ensure_api_key()
    assert os.getenv("OPENAI_API_KEY") == "gemini-value"


def test_analyse_success(monkeypatch):
    # prepare a valid JSON response from LLM
    valid = {
        "scores": {"structure": 10, "argument_depth": 20, "evidence_use": 30, "coherence": 40, "overall": 25},
        "band": "Pass",
        "strengths": [],
        "weaknesses": [],
        "revision_roadmap": [],
        "confidence": 0.5,
        "confidence_notes": "ok",
    }
    monkeypatch.setenv("OPENAI_API_KEY", "test")

    def fake_create(*args, **kwargs):
        return DummyResponse(json.dumps(valid))

    monkeypatch.setattr(scorer, "_get_client", lambda: DummyClient(fake_create))

    result = analyse_essay("essay", "Undergraduate", "General", "Critical Essay", False, 3)
    assert result["scores"]["structure"] == 10
    assert "rag_sources" in result


def test_analyse_llm_error(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test")

    def fail_create(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(scorer, "_get_client", lambda: DummyClient(fail_create))
    with pytest.raises(RuntimeError):
        analyse_essay("x", "a", "b", "c", False)


def test_analyse_invalid_json(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test")

    def fake_create(*args, **kwargs):
        return DummyResponse("not json")

    monkeypatch.setattr(scorer, "_get_client", lambda: DummyClient(fake_create))
    with pytest.raises(RuntimeError):
        analyse_essay("x", "a", "b", "c", False)
