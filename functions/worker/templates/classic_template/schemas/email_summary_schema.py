from pydantic import BaseModel, Field


class EmailSummarySchema(BaseModel):
    short_summary: str = Field(
        ...,
        description="A short, human-readable summary of the email content. One sentence max. Same language as input.",
    )
