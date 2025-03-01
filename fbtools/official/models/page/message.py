"""Messages field webhook.

A notification is sent when your business has received a message
from a customer from any conversation entry point.

For Instagram Messaging, this subscription will also include
notifications when your Instagram Professional account has
sent a message since there is no separate message_echoes
subscription field for Instagram Messaging.
"""

from typing import Literal
from pydantic import BaseModel, Field


class Message(BaseModel):
    """Messages field data.

    This is inside entry key that contains list
    of dictionary.

    Attributes:
        time: The time of the message.
        id: The id of the message.
        messaging: The messaging object data.

    """

    time: int
    id: str
    messages: list["MessageObject"] = Field(..., alias="messaging")


class MessageObject(BaseModel):
    """Messaging field data.

    This is data of a dictionary, embodies the
    messages field data.

    Attributes:
        sender: The sender of the message.
        recipient: The reciepient of the message.
        timestamp: The timestamp of the message.
        message: The message object data.

    """

    sender: "Sender"
    recipient: "Recipient"
    timestamp: int
    message: "MessageContent"


class Sender(BaseModel):
    """Sender id.

    Attributes:
        id: The id of the sender.

    """

    id: str


class Recipient(BaseModel):
    """Recipient id.

    Attributes:
        id: The id of the page.

    """

    id: str


class MessageContent(BaseModel):
    """Message.

    Contains the message object data.

    Attributes:
        mid: The message id of the message.
        text: The text of the message.
        reply_to: The reply to message that contains message id.
        quick_reply: The quick reply of the message that contains payload data.

    """

    mid: str
    text: str
    attachments: "Attachments | None"
    reply_to: "ReplyTo | None"
    quick_reply: "QuickReply | None"


class Attachments(BaseModel):
    """Attachments.

    Attributes:
        payload: The payload of the attachment.

    """

    attachment_type: Literal["image", "video", "audio", "file", "reel", "ig_reel"]
    payload: "AttachmentPayload"


class AttachmentPayload(BaseModel):
    """Attachment payload.

    Attributes:
        url: The url of the attachment.

    """

    url: str


class QuickReply(BaseModel):
    """Quick reply.

    Attributes:
        payload: The payload of the quick reply.

    """

    payload: str


class ReplyTo(BaseModel):
    """Reply to.

    Attributes:
        id: The id of the message it was replying to.

    """

    mid: str


Message.model_rebuild()
