"""Message edit webhook.

A notification is sent when someone edits a message.
"""

from pydantic import BaseModel


class MessageEditContent(BaseModel):
    """MessageEditContent data."""

    mid: str
    text: str
    num_edit: int
