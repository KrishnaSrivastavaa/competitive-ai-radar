from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.competitor import Competitor
from app.schemas.competitor import CompetitorCreate, CompetitorRead

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
