# Parses LLM JSON into structured objects and validates via pydantic

from typing import List, Literal, Optional
from pydantic import BaseModel, Field, ValidationError
import json


class ScoreModel(BaseModel):
    structure: int
    argument_depth: int
    evidence_use: int
    coherence: int
    overall: int


class StrengthWeakness(BaseModel):
    dimension: str
    point: str


class RoadmapItem(BaseModel):
    priority: int = Field(..., ge=1, le=7)
    dimension: str
    title: str
    action: str
    impact: Literal["High", "Medium", "Low"]
    effort: Literal["Quick fix", "Moderate", "Deep revision"]


class FeedbackModel(BaseModel):
    scores: ScoreModel
    band: Literal["Distinction", "Merit", "Pass", "Developing"]
    strengths: List[StrengthWeakness] = []
    weaknesses: List[StrengthWeakness] = []
    revision_roadmap: List[RoadmapItem] = []
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    confidence_notes: str = ""


def parse_feedback(raw_response: str) -> dict:
    """Validate a raw JSON string from the LLM and return a dict.

    Raises a ``ValueError`` if the response cannot be parsed or if the
    contents violate the expected schema.  The caller may catch this and
    present a user‑friendly error to the UI.
    """
    try:
        payload = json.loads(raw_response)
    except json.JSONDecodeError as exc:
        raise ValueError("response was not valid JSON") from exc

    try:
        fb = FeedbackModel(**payload)
    except ValidationError as exc:
        # include the validation errors in the exception message for easier
        # debugging / logging upstream
        raise ValueError(f"response failed schema validation: {exc}") from exc

    # ``model_dump`` is the v2 replacement for ``dict``; avoids deprecation
    return fb.model_dump()
