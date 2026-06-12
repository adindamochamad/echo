from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class Severity(str, Enum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"


class ActionItemStatus(str, Enum):
    COMPLETED = "COMPLETED"
    IN_PROGRESS = "IN_PROGRESS"
    OPEN = "OPEN"
    ABANDONED = "ABANDONED"
    NEVER_STARTED = "NEVER STARTED"


class ActionItem(BaseModel):
    description: str
    owner: Optional[str] = None
    status: ActionItemStatus = ActionItemStatus.OPEN
    ticket_ref: Optional[str] = None


class RecurrenceMatch(BaseModel):
    incident_id: str
    title: str
    incident_date: str
    similarity_score: float
    days_between: int = 0
    unimplemented_items: list[ActionItem] = []


class AnalyzeRequest(BaseModel):
    raw_content: str = Field(..., min_length=50, max_length=20000)
    severity_hint: Optional[Severity] = None

    @field_validator("raw_content")
    @classmethod
    def validasi_konten(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Content cannot be empty or whitespace only")
        return v


class AnalyzeResponse(BaseModel):
    summary: str
    root_causes: list[str]
    action_items: list[ActionItem]
    severity: Optional[Severity] = None
    systems_affected: list[str] = []
    recurrence_matches: list[RecurrenceMatch] = []


class ClimaxResponse(BaseModel):
    title: str
    incident_date: str
    severity: Severity
    summary: str
    systems_affected: list[str]
    similarity_score: float
    days_between: int
    matched_incident_title: str
    matched_incident_date: str
    unimplemented_items: list[ActionItem]
    echo_verdict: str


class PatternScoreResponse(BaseModel):
    score: int
    total_postmortems: int
    total_recurrences: int
    recurrence_rate: float
    avg_action_completion: float


class IncidentSummary(BaseModel):
    id: str
    title: str
    incident_date: str
    severity: Severity
    summary: str
    root_causes: list[str]
    action_items: list[ActionItem]
    systems_affected: list[str] = []
    has_recurrence: bool = False
