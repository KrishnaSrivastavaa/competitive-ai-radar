from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.collection_run import CollectionRun
    from app.models.source import Source


class Snapshot(Base):
    __tablename__ = "snapshots"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"), index=True)
    collection_run_id: Mapped[int] = mapped_column(
        ForeignKey("collection_runs.id"), unique=True, index=True
    )
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    content_hash: Mapped[str] = mapped_column(String(64), index=True)
    normalized_data: Mapped[Any] = mapped_column(JSON, nullable=False)
    evidence_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    source: Mapped["Source"] = relationship(back_populates="snapshots")
    collection_run: Mapped["CollectionRun"] = relationship(back_populates="snapshot")
