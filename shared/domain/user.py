import uuid
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict

from shared.domain.mail_account import MailAccount


class User(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={
            uuid.UUID: str,
        },
    )

    id: uuid.UUID
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    billing_address: Optional[Dict[str, Any]] = None
    payment_method: Optional[Dict[str, Any]] = None
    timezone_code: str

    mail_accounts: Optional[List[MailAccount]] = None

    def get_timezone(self) -> ZoneInfo:
        return ZoneInfo(self.timezone_code)
