import uuid
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class DeliveryChannelEnum(Enum):
    EMAIL = "EMAIL"
    TELEGRAM = "TELEGRAM"
    WHATSAPP = "WHATSAPP"


class DeliveryChannel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: uuid.UUID
    channel_type: DeliveryChannelEnum
    address: str
    is_active: bool = True
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def deactivate(self):
        self.is_active = False
        self.updated_at = datetime.now(timezone.utc)

    def activate(self):
        self.is_active = True
        self.updated_at = datetime.now(timezone.utc)
