import uuid
from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict


class User(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    billing_address: Optional[Dict[str, Any]] = None
    payment_method: Optional[Dict[str, Any]] = None
