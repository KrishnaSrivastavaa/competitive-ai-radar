from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class CollectionRunRead(BaseModel):
    id: int
    source_id: int
    status: str
    started_at: datetime
    finished_at: datetime | None
    raw_result: Any | None
    record_count: int
    error_message: str | None
    health_status: str
    bright_data_collection_id: str | None

    model_config = ConfigDict(from_attributes=True)


class ScraperCreateResponse(BaseModel):
    collector_id: str
    status: str
