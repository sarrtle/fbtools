"""Messaging webhook object."""

import json
from pydantic import BaseModel, ValidationError, model_validator

from fbtools.official.models.page.messaging.message_content import MessageContent
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

# types of messages
MessageTypes = (
    MessageContent
    | MessageEditContent
    | MessageOptinContent
    | MessageReactionContent
    | MessageReadContent
    | MessagingPostbackContent
    | MessagingReferralContent
)


class Message(BaseModel):
    """Messaging data."""

    sender: Sender
    recipient: Recipient
    timestamp: int
    message_type: MessageTypes

    @model_validator(mode="before")
    def _validate_message_type(cls, data: dict[str, str | MessageTypes]):
        """Validate message type.

        Dynamically determine message type base on the available data.
        """
        message_types = {
            "message": MessageContent,
            "message_edit": MessageEditContent,
            "optin": MessageOptinContent,
            "reaction": MessageReactionContent,
            "read": MessageReadContent,
            "postback": MessagingPostbackContent,
            "referral": MessagingReferralContent,
        }
        current_message_type = [name for name in message_types.keys() if name in data]
        # print(current_message_type, data)
        if len(current_message_type) != 1:
            raise ValueError(
                f"Expected one of {message_types} but got {current_message_type}"
            )

        field_name = current_message_type[0]
        field_data = data.pop(field_name)

        # validating here to see if there is a problem
        # of the data not matching the models
        try:
            model = message_types[field_name].model_validate(field_data)
        except ValidationError:
            print(
                f"ERROR on validating data for message_type: {field_name} on this data: {json.dumps(field_data, indent=4)}"
            )
            raise ValueError(
                f"Expected one of {message_types} but got {current_message_type}"
            )

        data["message_type"] = model

        return data
