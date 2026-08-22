from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, delete
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.competitor import Competitor
from app.schemas.competitor import CompetitorCreate, CompetitorRead
from app.models.insight import Insight
from app.services.brightdata import (
    BrightDataClient,
    BrightDataError,
    get_bright_data_client,
)

router = APIRouter(prefix="/competitors", tags=["competitors"])


@router.post("", response_model=CompetitorRead, status_code=status.HTTP_201_CREATED)
def create_competitor(payload: CompetitorCreate, db: Session = Depends(get_db)) -> Competitor:
    competitor = Competitor(**payload.model_dump(mode="json"))
    db.add(competitor)
    db.commit()
    db.refresh(competitor)
    return competitor


@router.get("", response_model=list[CompetitorRead])
def list_competitors(db: Session = Depends(get_db)) -> list[Competitor]:
    return list(db.scalars(select(Competitor).order_by(Competitor.id)))


@router.get("/{competitor_id}", response_model=CompetitorRead)
def get_competitor(competitor_id: int, db: Session = Depends(get_db)) -> Competitor:
    competitor = db.get(Competitor, competitor_id)
    if competitor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Competitor not found")
    return competitor


@router.delete("/{competitor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_competitor(
    competitor_id: int,
    db: Session = Depends(get_db),
    bright_data: BrightDataClient = Depends(get_bright_data_client),
) -> None:
    competitor = db.get(Competitor, competitor_id)

    if competitor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Competitor not found",
        )

    collector_ids = {
        source.collector_id
        for source in competitor.sources
        if source.collector_id
    }

    try:
        for collector_id in collector_ids:
            bright_data.delete_scraper(collector_id)
    except BrightDataError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Unable to delete Bright Data scraper: {exc}",
        ) from exc
    finally:
        bright_data.close()

    db.execute(
        delete(Insight).where(Insight.competitor_id == competitor_id)
    )

    db.delete(competitor)
    db.commit()