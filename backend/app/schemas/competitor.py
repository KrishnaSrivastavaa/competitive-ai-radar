from pydantic import BaseModel, ConfigDict, HttpUrl


class CompetitorCreate(BaseModel):
    name: str
    website_url: HttpUrl
    description: str | None = None
    active: bool = True


class CompetitorRead(CompetitorCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)
