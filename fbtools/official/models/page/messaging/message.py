"""Messaging webhook object."""

from pydantic import BaseModel, model_validator

from fbtools.official.models.page.messaging.message_content import MessageContent
from fbtools.official.models.page.messaging.message_echoes import MessageEchoContent
from fbtools.official.models.page.messaging.message_edit import MessageEditContent
from fbtools.official.models.page.messaging.message_optins import MessageOptinContent
from fbtools.official.models.page.messaging.message_reaction import (
    MessageReactionContent,
)
from fbtools.official.models.page.messaging.message_read import MessageReadContent
from fbtools.official.models.page.messaging.messaging_postback import (
    MessagingPostbackContent,
)
from fbtools.official.models.page.messaging.messaging_referral import (
    MessagingReferralContent,
)
from fbtools.official.models.page.messaging.models import Recipient, Sender


class Message(BaseModel):
    """Messaging data."""

    sender: Sender
    recipient: Recipient
    timestamp: int
    message_type: (
        MessageContent
        | MessageEchoContent
        | MessageEditContent
        | MessageOptinContent
        | MessageReactionContent
        | MessageReadContent
        | MessagingPostbackContent
        | MessagingReferralContent
    )

    @model_validator(mode="before")
    def _validate_message_type(cls, data: dict[str, str]):
        """Validate message type.

        Dynamically determine message type base on the available data.
        """
        message_types = [
            "message",
            "message_edit",
            "optin",
            "reaction",
            "read",
            "postback",
            "referral",
        ]
        current_message_type = [name for name in message_types if name in data]
        if len(current_message_type) != 1:
            raise ValueError(
                f"Expected one of {message_types} but got {current_message_type}"
            )

        field_name = current_message_type[0]
        data["message_type"] = data.pop(field_name)

        return data
