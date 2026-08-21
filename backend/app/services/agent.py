from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.change import Change
from app.models.competitor import Competitor
from app.models.insight import Insight
from app.models.snapshot import Snapshot
from app.models.source import Source
from app.schemas.agent import AgentAnswer
from app.services.llm_analysis import LLMClient

CHANGE_TERMS = ("change", "changed", "recent", "previous", "before")


class CompetitiveIntelligenceAgent:
    """Builds compact, competitor-scoped database context for Gemini."""

    def build_context(self, db: Session, competitor: Competitor, question: str) -> dict[str, Any]:
        sources = list(
            db.scalars(
                select(Source).where(Source.competitor_id == competitor.id, Source.active.is_(True))
            )
        )
        selected_sources: list[dict[str, Any]] = []
        source_ids: list[int] = []
        for source in sources:
            snapshot = db.scalar(
                select(Snapshot)
                .where(Snapshot.source_id == source.id)
                .order_by(Snapshot.captured_at.desc(), Snapshot.id.desc())
                .limit(1)
            )
            if snapshot is None:
                continue
            source_ids.append(source.id)
            selected_sources.append(
                {
                    "name": source.name,
                    "url": source.url,
                    "snapshot_captured_at": snapshot.captured_at.isoformat(),
                    "data": snapshot.normalized_data,
                }
            )

        context: dict[str, Any] = {
            "competitor": {"name": competitor.name, "description": competitor.description},
            "sources": selected_sources,
        }
        if any(term in question.lower() for term in CHANGE_TERMS) and source_ids:
            changes = list(
                db.scalars(
                    select(Change)
                    .where(Change.source_id.in_(source_ids), Change.change_type != "initial")
                    .order_by(Change.id.desc())
                    .limit(10)
                )
            )
            context["recent_verified_changes"] = [
                {"source_id": item.source_id, "type": item.change_type, "summary": item.summary, "diff_data": item.diff_data, "significance": item.significance}
                for item in changes
            ]
        return context

    def answer(self, db: Session, competitor: Competitor, question: str, llm: LLMClient) -> AgentAnswer:
        context = self.build_context(db, competitor, question)
        if not context["sources"]:
            raise ValueError("Competitor has no stored snapshots from active sources")
        answer = AgentAnswer.model_validate(llm.answer_question(context, question))
        allowed_urls = {source["url"] for source in context["sources"]}
        if any(item.source_url not in allowed_urls for item in answer.evidence):
            raise ValueError("Gemini returned evidence outside the stored source URLs")
        return answer
