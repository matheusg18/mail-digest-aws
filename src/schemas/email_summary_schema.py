from typing import List, Literal

from pydantic import BaseModel, Field


class EmailSummarySchema(BaseModel):
    summary: str = Field(..., description="Summary of the email content")
    priority: Literal["high", "medium", "low"] = Field(
        ..., description="Priority of the email (high/medium/low)"
    )
    type: Literal["event", "decision", "info", "action"] = Field(
        ..., description="Type of the email (event/decision/info/action)"
    )
    deadline: str | None = Field(
        None,
        description=(
            "Deadline for any actions required from the email if applicable"
        ),
    )
    involved_people: List[str] = Field(
        [], description="List of people involved in the email discussion"
    )
