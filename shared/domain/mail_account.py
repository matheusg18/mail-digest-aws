import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class EmailProviderEnum(Enum):
    GMAIL = "GMAIL"
    OUTLOOK = "OUTLOOK"


class MailAccount(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            uuid.UUID: str,
            datetime: lambda v: v.isoformat(),
        },
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    user_id: uuid.UUID
    provider: EmailProviderEnum
    email_address: str
    credentials: Optional[Dict[str, Any]] = None
    is_active: bool = True
