"""Messages field webhook.

A notification is sent when your business has received a message
from a customer from any conversation entry point.

For Instagram Messaging, this subscription will also include
notifications when your Instagram Professional account has
sent a message since there is no separate message_echoes
subscription field for Instagram Messaging.
"""

from pydantic import BaseModel, Field


class _Sender(BaseModel):
    """Sender id.

    Attributes:
        id: The id of the sender.

    """

    id: str


class _Recipient(BaseModel):
    """Recipient id.

    Attributes:
        id: The id of the page.

    """

    id: str


class _QuickReply(BaseModel):
    """Quick reply.

    Attributes:
        payload: The payload of the quick reply.

    """

    payload: str


class _ReplyTo(BaseModel):
    """Reply to.

    Attributes:
        id: The id of the message it was replying to.

    """

    mid: str


class _Message(BaseModel):
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
    reply_to: _ReplyTo | None
    quick_reply: _QuickReply | None


class _Messaging(BaseModel):
    """Messaging field data.

    This is data of a dictionary, embodies the
    messages field data.

    Attributes:
        sender: The sender of the message.
        recipient: The reciepient of the message.
        timestamp: The timestamp of the message.
        message: The message object data.

    """

    sender: _Sender
    recipient: _Recipient
    timestamp: int
    message: _Message


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
    messages: list[_Messaging] = Field(..., alias="messaging")
