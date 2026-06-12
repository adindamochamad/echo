from datetime import date
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.demo import ActionItem, RecurrenceMatch, Severity


class PostmortemCreate(BaseModel):
    title: str = Field(..., max_length=500)
    incident_date: date
    raw_content: str = Field(..., min_length=50, max_length=20000)
    severity: Optional[Severity] = None


class PostmortemOut(BaseModel):
    id: str
    title: str
    incident_date: str
    severity: Optional[Severity] = None
    summary: str
    root_causes: list[str] = []
    action_items: list[ActionItem] = []
    systems_affected: list[str] = []
    has_recurrence: bool = False
    recurrence_matches: list[RecurrenceMatch] = []

    model_config = {"from_attributes": True}
