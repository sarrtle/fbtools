"""Message object.

This object will have full control of how you
handle a message.

Docs references:
1. https://developers.facebook.com/docs/messenger-platform/send-messages/
"""

from typing import Literal
from fbtools.official.models.extra.facebook_message_attachment import (
    FbMessageAttachment_Dict,
)
from fbtools.official.models.response.facebook_message_response import (
    FacebookMessageResponse,
)
from fbtools.official.utilities.common import create_url_format, get_attachment_mimetype

from httpx import AsyncClient, HTTPStatusError


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
    async def send_text(self, text: str) -> "FacebookMessage":
        """Send a normal text.

        Notes:
            Why this is separated from send_attachment is because you can only
            send one message type at once like if it is a text then it is a text,
            if it is an attachment then it is an attachment.

        Args:
            text: The text of the message
            attachments: The attachments of the message that can be url, file, attachment id

        """
        data: dict[str, object] = {"message": {"text": text}}

        facebook_message_object = await self._send_api(data)
        return facebook_message_object

    async def send_attachment(
        self,
        attachments: (
            str | FbMessageAttachment_Dict | list[str | FbMessageAttachment_Dict]
        ),
    ) -> "FacebookMessage":
        """Send an attachment to Facebook messenger.

        Notes:
            You can also send multiple attachments at once.

        Notes:
            The method of sending an attachment is separated for
            following reasons:
            1. You are sending repeated images like banner, notification and
                you are sure that the attachment url is stable and it is the
                type that you are expecting. This is fast and reliable so
                performance matters in your code but this is unsafe and you
                are expecting an error after sending an API request to facebook
                if something went wrong with the attachment url you used.
                - use dictionary format
            2. You just want to provide a string url or filepath or attachment id
                or you don't know what type of the attachment you are sending.
                The algorithm will handle attachment type for you. It can give you
                early errors and it has a network overhead if attachment url and
                attachment id but none on local file.

                You can send an attachment url, filepath, attachment id or you don't know what type
                - use list of string

        Notes:
            One error from the attachment provided will fail the rest. This to ensure that all
            attachments are sent properly and developers should be responsible for using a
            stable image source.

        Args:
            attachments: The attachments of the message that can be url, file, attachment id

        Returns:
            a FacebookMessage object

        """
        attachment_data_list: list[dict[str, object]] = []

        if not isinstance(attachments, list):
            attachments = [attachments]

        for attachment in attachments:
            if isinstance(attachment, str):
                try:
                    attachment_type = await get_attachment_mimetype(
                        attachment=attachment, session=self._session
                    )

                except HTTPStatusError as hse:
                    raise Exception(
                        "Something went wrong from requesting to image url header"
                        + f"\n{hse}"
                    )
                except Exception:
                    raise Exception(
                        "Invalid attachment source. Check if it is really a valid url or a valid local path."
                    )

                # TODO: check if local file, needs to upload the local file to
                #       facebook server and get the attachment id
                attachment_data_list.append(
                    {
                        "type": attachment_type,
                        "payload": {"url": attachment, "is_reusable": True},
                    }
                )
            else:
                # validate
                if (
                    "source" not in attachment.keys()
                    and "attachment_type" not in attachment.keys()
                ):
                    raise Exception(
                        "Invalid attachment type, please use the proper dictionary format."
                    )

                attachment_data_list.append(
                    {
                        "type": attachment["attachment_type"],
                        "payload": {"url": attachment["source"], "is_reusable": True},
                    }
                )

        data: dict[str, object] = {"message": {"attachments": attachment_data_list}}

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
