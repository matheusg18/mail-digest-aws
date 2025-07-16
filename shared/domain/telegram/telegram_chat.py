from typing import Literal

from gotrue import Optional
from pydantic import BaseModel, ConfigDict


class TelegramChat(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: Literal["private", "group", "supergroup", "channel"]
    username: Optional[str] = None
