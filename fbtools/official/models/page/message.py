"""Message object.

This object will have full control of how you
handle a message.

Docs references:
1. https://developers.facebook.com/docs/messenger-platform/send-messages/
"""

from os.path import exists
from typing import Literal
from fbtools.official.models.response.facebook_message_response import (
    FacebookMessageResponse,
)
from fbtools.official.utilities.common import create_url_format

from httpx import AsyncClient


class FacebookMessage:
    """FacebookMessage object."""

    def __init__(
        self,
        sender: str,
        recipient: str,
        timestamp: int,
        message_id: str,
        session: AsyncClient,
        access_token: str,
        user_id: str | Literal["me"] = "me",
    ) -> None:
        """Initialize FacebookMessage.

        Args:
            sender: The sender id
            recipient: The recipient id
            timestamp: The timestamp of the message
            message_id: The message id
            session: The httpx async session object
            access_token: The page access token
            user_id: The user id or "me". The "me" is used on dev mode.

        """
        # important variables
        self._sender: str = sender
        self._recipient: str = recipient
        self._timestamp: int = timestamp

        # important inner variables
        self._user_id: str = user_id
        self._session: AsyncClient = session
        self._response_type: Literal["RESPONSE", "UPDATES", "TAGGED MESSAGE"] = (
            "RESPONSE"
        )
        self._headers: dict[str, str] = {"Content-Type": "application/json"}
        self._access_token: str = access_token

    # PUBlIC METHODS
    # ----------------------------------------
    async def send_text(
        self, text: str | None = None, attachments: str | list[str] | None = None
    ) -> "FacebookMessage":
        """Send a normal text.

        Args:
            text: The text of the message
            attachments: The attachments of the message that can be url, file, attachment id

        """
        data: dict[str, object] = {}
        data["message"] = {}
        attachment_data: list[dict[str, object]] = []

        if not isinstance(attachments, list):
            attachments = [attachments] if attachments is not None else []

        data.update({"message": {"text": text if text is not None else ""}})

        for attachment in attachments:
            # separately preprocess the local file
            # - url
            if attachment.startswith("http"):
                attachment_data.append(
                    {"type": "image", "payload": {"url": attachment}}
                )
            # - attachment id
            elif attachment.isdigit():
                attachment_data.append(
                    {"type": "image", "payload": {"attachment_id": attachment}}
                )
            # - local file
            elif exists(attachment):
                # TODO: upload local file, implement asynchronous upload if many local file
                raise NotImplementedError
            else:
                raise Exception(f"Attachment {attachment} is not valid.")

        if len(attachment_data) > 0:
            data["message"].update({"attachments": attachment_data})

        facebook_message_object = await self._send_api(data)
        return facebook_message_object

    # OBJECT CONTROL
    # ----------------------------------------
    def set_response_type(
        self, response_type: Literal["RESPONSE", "UPDATES", "TAGGED MESSAGE"]
    ):
        """Set the response type.

        Default is "RESPONSE".
        """
        self._response_type = response_type

    # PRIVATE METHODS
    # ----------------------------------------
    async def _send_api(self, data: dict[str, object]) -> "FacebookMessage":
        """Centralize of sending data to the API."""
        # preprocess data
        # - automatically use sender id as a recipient for sending messages back
        data.update({"recipient": {"id": self._sender}})
        # - set response type
        data.update({"messaging_type": self._response_type})
        # - set params and url
        params = {"access_token": self._access_token}
        url = create_url_format(f"{self._user_id}/messages")

        # send and validate
        response = await self._session.post(
            url=url, json=data, params=params, headers=self._headers
        )
        # print(response.json())

        facebook_message_response_object = FacebookMessageResponse.model_validate(
            response.json()
        )
        # - sender is now recipient and recipient (the page) is now the sender
        facebook_message_object = FacebookMessage(
            sender=self._recipient,
            recipient=self._sender,
            # TODO: Do accurate timestamp, probably using datetime
            timestamp=self._timestamp,
            message_id=facebook_message_response_object.message_id,
            session=self._session,
            access_token=self._access_token,
            user_id=self._user_id,
        )

        return facebook_message_object
