from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.change import Change
from app.models.competitor import Competitor
from app.models.insight import Insight
from app.models.snapshot import Snapshot
from app.models.source import Source
from app.schemas.insight import InsightAnalysis, InsightRead
from app.services.llm_analysis import LLMClient, LLMError, LLMTimeoutError, get_llm_client

router = APIRouter(tags=["insights"])


def _analysis_evidence(change: Change, source: Source, competitor: Competitor, current: Snapshot, previous: Snapshot | None) -> dict[str, Any]:
    return {
        "competitor": {"name": competitor.name, "description": competitor.description},
        "source": {"name": source.name, "url": source.url},
        "verified_change": {
            "type": change.change_type,
            "summary": change.summary,
            "diff_data": change.diff_data,
        },
        "previous_snapshot_data": previous.normalized_data if previous else None,
        "current_snapshot_data": current.normalized_data,
    }


@router.post("/changes/{change_id}/analyze", response_model=InsightRead, status_code=status.HTTP_201_CREATED)
def analyze_change(change_id: int, db: Session = Depends(get_db), llm: LLMClient = Depends(get_llm_client)) -> Insight:
    change = db.get(Change, change_id)
    if change is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Change not found")
    if change.change_type in {"initial", "unchanged"}:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only added, removed, or modified changes can be analyzed")

    current = db.get(Snapshot, change.current_snapshot_id)
    source = db.get(Source, change.source_id)
    if current is None or source is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Change evidence is incomplete")
    competitor = db.get(Competitor, source.competitor_id)
    if competitor is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Change competitor is missing")
    previous = db.get(Snapshot, change.previous_snapshot_id) if change.previous_snapshot_id else None

    try:
        analysis = InsightAnalysis.model_validate(
            llm.analyze_change(_analysis_evidence(change, source, competitor, current, previous))
        )
    except LLMTimeoutError as exc:
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail="Gemini analysis timed out") from exc
    except (LLMError, ValidationError) as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Gemini returned no valid analysis") from exc

    insight = Insight(
        competitor_id=competitor.id,
        change_id=change.id,
        **analysis.model_dump(mode="json"),
    )
    db.add(insight)
    db.commit()
    db.refresh(insight)
    return insight


@router.get("/insights/{insight_id}", response_model=InsightRead)
def get_insight(insight_id: int, db: Session = Depends(get_db)) -> Insight:
    insight = db.get(Insight, insight_id)
    if insight is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Insight not found")
    return insight


@router.get("/competitors/{competitor_id}/insights", response_model=list[InsightRead])
def list_competitor_insights(competitor_id: int, db: Session = Depends(get_db)) -> list[Insight]:
    if db.get(Competitor, competitor_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Competitor not found")
    return list(
        db.scalars(
            select(Insight).where(Insight.competitor_id == competitor_id).order_by(Insight.id.desc())
        )
    )
