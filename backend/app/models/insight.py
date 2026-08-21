from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, Float, ForeignKey, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.change import Change
    from app.models.competitor import Competitor


class Insight(Base):
    __tablename__ = "insights"

    id: Mapped[int] = mapped_column(primary_key=True)
    competitor_id: Mapped[int] = mapped_column(ForeignKey("competitors.id"), index=True)
    change_id: Mapped[int | None] = mapped_column(ForeignKey("changes.id"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    analysis: Mapped[str] = mapped_column(Text, nullable=False)
    competitive_impact: Mapped[str] = mapped_column(Text, nullable=False)
    recommendation: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    evidence: Mapped[Any] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    competitor: Mapped["Competitor"] = relationship(back_populates="insights")
    change: Mapped["Change | None"] = relationship(back_populates="insights")
