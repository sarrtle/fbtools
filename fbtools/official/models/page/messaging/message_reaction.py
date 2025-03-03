"""Message reactions webhook field.

A notification is sent when someone reacts to a message.
"""

from typing import Literal
from pydantic import BaseModel


class MessageReactionContent(BaseModel):
    """Message React data.

    Attributes:
        mid: The message id of the message.
        action: The action of the reaction. React or unreact.
        emoji: The emoji of the reaction.
        reaction: The description of the reaction.

    """

    mid: str
    action: Literal["react", "unreact"]
    emoji: str | None
    reaction: str | None
