from pydantic import BaseModel, Field


class AgentQuestion(BaseModel):
    question: str = Field(min_length=1)


class AgentEvidenceItem(BaseModel):
    source_url: str
    source_name: str
    reason: str


class AgentAnswer(BaseModel):
    answer: str
    evidence: list[AgentEvidenceItem]
