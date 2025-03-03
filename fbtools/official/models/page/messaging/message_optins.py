"""Message optins content."""

from typing import Literal
from pydantic import BaseModel


class MessageOptinContent(BaseModel):
    """Message optins content."""

    type: Literal["notification_messages"]
    payload: str
    notification_messages_token: str
    notification_messages_frequency: Literal["daily"]
    token_expiration_timestamp: int
    user_token_status: Literal["REFRESHED"]
