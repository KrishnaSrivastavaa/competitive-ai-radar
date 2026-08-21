from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.competitor import Competitor
from app.schemas.agent import AgentAnswer, AgentQuestion
from app.services.agent import CompetitiveIntelligenceAgent
from app.services.llm_analysis import LLMClient, LLMError, LLMTimeoutError, get_llm_client

router = APIRouter(tags=["competitive-intelligence-agent"])


@router.post("/competitors/{competitor_id}/ask", response_model=AgentAnswer)
def ask_competitor(
    competitor_id: int,
    payload: AgentQuestion,
    db: Session = Depends(get_db),
    llm: LLMClient = Depends(get_llm_client),
) -> AgentAnswer:
    competitor = db.get(Competitor, competitor_id)
    if competitor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Competitor not found")
    if not payload.question.strip():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Question must not be empty")
    try:
        return CompetitiveIntelligenceAgent().answer(db, competitor, payload.question, llm)
    except LLMTimeoutError as exc:
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail="Gemini agent request timed out") from exc
    except LLMError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Gemini returned no valid answer") from exc
    except (ValueError, ValidationError) as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
