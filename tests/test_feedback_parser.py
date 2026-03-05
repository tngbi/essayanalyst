import sys, os
import pytest
import json

# ensure workspace root is importable
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from analyst.feedback_parser import parse_feedback

VALID_RESPONSE = {
    "scores": {
        "structure": 80,
        "argument_depth": 70,
        "evidence_use": 60,
        "coherence": 90,
        "overall": 75,
    },
    "band": "Merit",
    "strengths": [{"dimension": "Structure", "point": "Well-organised."}],
    "weaknesses": [{"dimension": "Evidence", "point": "Needs more citations."}],
    "revision_roadmap": [
        {
            "priority": 1,
            "dimension": "Evidence",
            "title": "Add sources",
            "action": "Include two recent studies.",
            "impact": "High",
            "effort": "Moderate",
        }
    ],
    "confidence": 0.85,
    "confidence_notes": "Model was fairly sure.",
}


def test_parse_valid_response():
    json_str = json.dumps(VALID_RESPONSE)
    result = parse_feedback(json_str)
    assert result["scores"]["overall"] == 75
    assert result["band"] == "Merit"
    assert isinstance(result["revision_roadmap"], list)


def test_parse_invalid_json():
    with pytest.raises(ValueError):
        parse_feedback("not a json")


def test_parse_wrong_schema():
    bad = VALID_RESPONSE.copy()
    bad["scores"] = {"structure": 50}  # missing other fields
    with pytest.raises(ValueError):
        parse_feedback(json.dumps(bad))
