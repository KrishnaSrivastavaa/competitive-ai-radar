from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class SnapshotRead(BaseModel):
    id: int
    source_id: int
    collection_run_id: int
    captured_at: datetime
    content_hash: str
    normalized_data: Any
    evidence_url: str | None

    model_config = ConfigDict(from_attributes=True)
