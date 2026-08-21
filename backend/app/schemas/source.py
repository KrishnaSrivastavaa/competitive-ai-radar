from pydantic import BaseModel, ConfigDict, HttpUrl


class SourceCreate(BaseModel):
    name: str
    url: HttpUrl
    source_type: str = "website"
    active: bool = True
    extraction_description: str | None = None


class SourceRead(SourceCreate):
    id: int
    competitor_id: int
    collector_id: str | None

    model_config = ConfigDict(from_attributes=True)
