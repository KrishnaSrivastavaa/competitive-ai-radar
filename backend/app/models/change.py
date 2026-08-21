from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.insight import Insight
    from app.models.source import Source


class Change(Base):
    __tablename__ = "changes"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"), index=True)
    previous_snapshot_id: Mapped[int | None] = mapped_column(ForeignKey("snapshots.id"), nullable=True)
    current_snapshot_id: Mapped[int] = mapped_column(ForeignKey("snapshots.id"), index=True)
    change_type: Mapped[str] = mapped_column(String(50), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    diff_data: Mapped[Any] = mapped_column(JSON, nullable=False)
    significance: Mapped[str] = mapped_column(String(50), nullable=False)

    source: Mapped["Source"] = relationship(back_populates="changes")
    insights: Mapped[list["Insight"]] = relationship(back_populates="change")
