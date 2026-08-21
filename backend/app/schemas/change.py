from typing import Any

from pydantic import BaseModel, ConfigDict


class ChangeRead(BaseModel):
    id: int
    source_id: int
    previous_snapshot_id: int | None
    current_snapshot_id: int
    change_type: str
    summary: str
    diff_data: Any
    significance: str

    model_config = ConfigDict(from_attributes=True)
