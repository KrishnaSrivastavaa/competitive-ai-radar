from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.competitor import Competitor
from app.models.change import Change
from app.models.collection_run import CollectionRun
from app.models.snapshot import Snapshot
from app.models.source import Source
from app.schemas.change import ChangeRead
from app.schemas.collection_run import CollectionRunRead, ScraperCreateResponse
from app.schemas.snapshot import SnapshotRead
from app.schemas.source import SourceCreate, SourceRead
from app.services.brightdata import (
    BrightDataClient,
    BrightDataError,
    BrightDataTimeoutError,
    get_bright_data_client,
)
from app.services.change_detection import detect_changes
from app.services.normalization import compute_content_hash, normalize_result

router = APIRouter(tags=["sources"])


@router.post(
    "/competitors/{competitor_id}/sources",
    response_model=SourceRead,
    status_code=status.HTTP_201_CREATED,
)
def create_source(
    competitor_id: int, payload: SourceCreate, db: Session = Depends(get_db)
) -> Source:
    if db.get(Competitor, competitor_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Competitor not found")

    source = Source(competitor_id=competitor_id, **payload.model_dump(mode="json"))
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


@router.get("/competitors/{competitor_id}/sources", response_model=list[SourceRead])
def list_competitor_sources(competitor_id: int, db: Session = Depends(get_db)) -> list[Source]:
    if db.get(Competitor, competitor_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Competitor not found")
    return list(
        db.scalars(
            select(Source).where(Source.competitor_id == competitor_id).order_by(Source.id)
        )
    )


@router.get("/sources/{source_id}", response_model=SourceRead)
def get_source(source_id: int, db: Session = Depends(get_db)) -> Source:
    source = db.get(Source, source_id)
    if source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")
    return source


@router.post("/sources/{source_id}/scraper", response_model=ScraperCreateResponse)
def create_scraper(
    source_id: int,
    db: Session = Depends(get_db),
    bright_data: BrightDataClient = Depends(get_bright_data_client),
) -> ScraperCreateResponse:
    source = db.get(Source, source_id)
    if source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")
    if not source.extraction_description:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Source requires an extraction_description before creating a scraper",
        )

    try:
        collector_id = bright_data.create_scraper(
            name=source.name,
            url=source.url,
            description=source.extraction_description,
        )
    except BrightDataTimeoutError as exc:
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=str(exc)) from exc
    except BrightDataError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    source.collector_id = collector_id
    db.commit()
    return ScraperCreateResponse(collector_id=collector_id, status="done")


@router.post("/sources/{source_id}/collect", response_model=CollectionRunRead)
def collect_source(
    source_id: int,
    db: Session = Depends(get_db),
    bright_data: BrightDataClient = Depends(get_bright_data_client),
) -> CollectionRun:
    source = db.get(Source, source_id)
    if source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")
    if not source.active:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Source is inactive")
    if not source.collector_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Source has no configured Bright Data collector",
        )

    run = CollectionRun(source_id=source.id, status="running", health_status="unknown")
    db.add(run)
    db.commit()
    db.refresh(run)

    try:
        collection_id, result = bright_data.collect(source.collector_id, source.url)
        run.bright_data_collection_id = collection_id
        run.raw_result = result
        run.finished_at = datetime.now(timezone.utc)
        if isinstance(result, list):
            run.status = "succeeded"
            run.record_count = len(result)
            run.health_status = "healthy" if result else "degraded"
        else:
            run.status = "succeeded"
            run.record_count = 0
            run.health_status = "degraded"
            run.error_message = "Bright Data returned an unexpected dataset format"
    except BrightDataError as exc:
        run.status = "failed"
        run.health_status = "failed"
        run.error_message = str(exc)
        run.finished_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(run)

    if run.status == "succeeded" and isinstance(run.raw_result, list):
        try:
            normalized_result = normalize_result(run.raw_result)
            previous_snapshot = db.scalar(
                select(Snapshot)
                .where(Snapshot.source_id == source.id)
                .order_by(Snapshot.id.desc())
                .limit(1)
            )
            snapshot = Snapshot(
                source_id=source.id,
                collection_run_id=run.id,
                captured_at=datetime.now(timezone.utc),
                content_hash=compute_content_hash(normalized_result),
                normalized_data=normalized_result,
                evidence_url=source.url,
            )
            db.add(snapshot)
            db.flush()
            detected = detect_changes(
                previous_data=previous_snapshot.normalized_data if previous_snapshot else None,
                current_data=normalized_result,
                previous_hash=previous_snapshot.content_hash if previous_snapshot else None,
                current_hash=snapshot.content_hash,
            )
            db.add(
                Change(
                    source_id=source.id,
                    previous_snapshot_id=previous_snapshot.id if previous_snapshot else None,
                    current_snapshot_id=snapshot.id,
                    change_type=detected.change_type,
                    summary=detected.summary,
                    diff_data=detected.diff_data,
                    significance=detected.significance,
                )
            )
            db.commit()
        except Exception as exc:
            db.rollback()
            run.error_message = f"Snapshot/change processing failed: {exc}"
            db.commit()

    db.refresh(run)
    return run


@router.get("/sources/{source_id}/runs", response_model=list[CollectionRunRead])
def list_collection_runs(source_id: int, db: Session = Depends(get_db)) -> list[CollectionRun]:
    if db.get(Source, source_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")
    return list(
        db.scalars(
            select(CollectionRun)
            .where(CollectionRun.source_id == source_id)
            .order_by(CollectionRun.id.desc())
        )
    )


@router.get("/sources/{source_id}/snapshots", response_model=list[SnapshotRead])
def list_snapshots(source_id: int, db: Session = Depends(get_db)) -> list[Snapshot]:
    if db.get(Source, source_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")
    return list(
        db.scalars(
            select(Snapshot).where(Snapshot.source_id == source_id).order_by(Snapshot.id.desc())
        )
    )


@router.get("/sources/{source_id}/changes", response_model=list[ChangeRead])
def list_changes(source_id: int, db: Session = Depends(get_db)) -> list[Change]:
    if db.get(Source, source_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")
    return list(
        db.scalars(select(Change).where(Change.source_id == source_id).order_by(Change.id.desc()))
    )


@router.get("/changes/{change_id}", response_model=ChangeRead)
def get_change(change_id: int, db: Session = Depends(get_db)) -> Change:
    change = db.get(Change, change_id)
    if change is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Change not found")
    return change
