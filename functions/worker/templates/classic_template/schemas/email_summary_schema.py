from pydantic import BaseModel, Field


class EmailSummarySchema(BaseModel):
    short_summary: str = Field(
        ...,
        description="A short, human-readable summary of the email content. One sentence max.",
    )
    emoji: str = Field(
        ...,
        description="An emoji representing the email content. Should be a single emoji character.",
    )
