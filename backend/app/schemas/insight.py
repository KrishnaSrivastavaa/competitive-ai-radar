from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class EvidenceItem(BaseModel):
    source_url: str
    reason: str


class InsightAnalysis(BaseModel):
    title: str
    analysis: str
    competitive_impact: str
    recommendation: str
    confidence: float = Field(ge=0, le=1)
    evidence: list[EvidenceItem]


class InsightRead(InsightAnalysis):
    id: int
    competitor_id: int
    change_id: int | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
