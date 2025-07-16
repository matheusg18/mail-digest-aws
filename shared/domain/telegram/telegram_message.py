from gotrue import Optional
from pydantic import BaseModel, ConfigDict

from shared.domain.telegram.telegram_chat import TelegramChat


class TelegramMessage(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    message_id: int
    text: Optional[str]
    chat: Optional[TelegramChat]
