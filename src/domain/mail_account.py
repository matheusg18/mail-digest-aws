import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class EmailServiceEnum(Enum):
    GMAIL = "GMAIL"
    OUTLOOK = "OUTLOOK"


class MailAccount(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    user_id: uuid.UUID
    service_type: EmailServiceEnum
    account_email: str
    credentials: Optional[Dict[str, Any]] = None
    is_active: bool = True

    def deactivate(self):
        self.is_active = False
        self.updated_at = datetime.now(timezone.utc)

    def activate(self):
        self.is_active = True
        self.updated_at = datetime.now(timezone.utc)

    def update_credentials(self, new_credentials: Dict[str, Any]):
        self.credentials = new_credentials
        self.updated_at = datetime.now(timezone.utc)
