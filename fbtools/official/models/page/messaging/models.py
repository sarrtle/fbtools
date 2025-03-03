"""Reusable and importable models for messaging."""

from pydantic import BaseModel



class Sender(BaseModel):
    """Sender data."""

    id: str


class Recipient(BaseModel):
    """Recipient data."""

    id: str


class Attachment(BaseModel):
    """Attachment payload data."""

    url: str


class QuickReply(BaseModel):
    """Quick reply data."""

    payload: str


class ReplyTo(BaseModel):
    """Reply to data."""

    mid: str
