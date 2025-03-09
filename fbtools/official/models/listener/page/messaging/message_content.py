"""Message content of messaging type."""

from pydantic import BaseModel

from fbtools.official.models.listener.page.messaging.models import (
    Attachment,
    QuickReply,
    ReplyTo,
)


class MessageContent(BaseModel):
    """Message content.

    Notes:
        message_echoes webhook event is merged on this
        object model because they have the same message
        type: `message` and probably same unpredictable data
        of `reply_to`, `attachments`. The only difference
        is when `is_echo` is True, it means that the message
        was sent by the page.

    Attributes:
        mid: The id of the message.
        text: The text content of the message.
        attachments: The attachments of the message.
        reply_to: The reply to of the message.
        quick_reply: The quick reply of the message.
        is_echo: Whether the message is sent by the page.

    """

    mid: str
    text: str | None = None
    attachments: list[Attachment] | None = None
    reply_to: ReplyTo | None = None
    quick_reply: QuickReply | None = None
    is_echo: bool = False
