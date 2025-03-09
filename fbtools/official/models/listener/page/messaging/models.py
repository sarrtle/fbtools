"""Reusable and importable models for messaging."""

from typing import Literal
from pydantic import BaseModel


class Sender(BaseModel):
    """Sender data."""

    id: str


class Recipient(BaseModel):
    """Recipient data."""

    id: str


class AttachmentPayload(BaseModel):
    """Payload for the attachment."""

    url: str
    title: str


class Attachment(BaseModel):
    """Attachment payload data."""

    type: Literal["image", "audio", "video", "file", "fallback"]
    payload: AttachmentPayload


class QuickReply(BaseModel):
    """Quick reply data."""

    payload: str


class ReplyTo(BaseModel):
    """Reply to data."""

    mid: str
