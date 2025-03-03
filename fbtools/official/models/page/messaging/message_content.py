"""Message content of messaging type."""

from pydantic import BaseModel

from fbtools.official.models.page.messaging.models import (
    Attachment,
    QuickReply,
    ReplyTo,
)


class MessageContent(BaseModel):
    """Message content."""

    mid: str
    text: str
    attachments: Attachment | None
    reply_to: ReplyTo | None
    quick_reply: QuickReply | None
