"""Messages field webhook.

Handles recieving messages from page.
"""

from pydantic import BaseModel


class _Sender(BaseModel):
    """Sender id."""

    id: str


class _Recipient(BaseModel):
    """Recipient id."""

    id: str


class _Message(BaseModel):
    """Message.

    Contains message id and text.
    """

    mid: str
    text: str


class _Messaging(BaseModel):
    """Messaging field data.

    This is data of a dictionary, embodies the
    messages field data.
    """

    sender: _Sender
    reciepient: _Recipient
    timestamp: int
    message: _Message


class Messages(BaseModel):
    """Messages field data.

    This is inside entry key that contains list
    of dictionary.
    """

    time: int
    id: str
    messaging: list[_Messaging]
