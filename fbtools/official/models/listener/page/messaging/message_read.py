"""Message read webhook data.

A notification is sent when someone reads a message.
"""

from pydantic import BaseModel


class MessageReadContent(BaseModel):
    """Message read data."""

    watermark: int
