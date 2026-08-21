from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.competitor import Competitor
    from app.models.collection_run import CollectionRun
    from app.models.snapshot import Snapshot
    from app.models.change import Change


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    competitor_id: Mapped[int] = mapped_column(ForeignKey("competitors.id"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    url: Mapped[str] = mapped_column(String(2048))
    source_type: Mapped[str] = mapped_column(String(100), default="website", nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    collector_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    extraction_description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    competitor: Mapped["Competitor"] = relationship(back_populates="sources")
    collection_runs: Mapped[list["CollectionRun"]] = relationship(
        back_populates="source", cascade="all, delete-orphan"
    )
    snapshots: Mapped[list["Snapshot"]] = relationship(
        back_populates="source", cascade="all, delete-orphan"
    )
    changes: Mapped[list["Change"]] = relationship(
        back_populates="source", cascade="all, delete-orphan"
    )
