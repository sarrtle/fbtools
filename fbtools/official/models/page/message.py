"""Message object.

This object will have full control of how you
handle a message.

Docs references:
1. https://developers.facebook.com/docs/messenger-platform/send-messages/
"""

import json
from os.path import basename, exists
from typing import Hashable, Literal, cast

from pydantic import ValidationError

from fbtools.official.models.extra.facebook_message_attachment import (
    FbMessageAttachment_Dict,
)
from fbtools.official.models.extra.facebook_message_template_models import (
    ButtonTemplatePostBack_Dict,
    ButtonTemplateWeb_Dict,
    GenericTemplate_Dict,
    QuickReplies_Dict,
)
from fbtools.official.models.listener.page.messaging.models import Attachment
from fbtools.official.models.response.facebook_message_response import (
    FacebookMessageResponse,
)
from fbtools.official.utilities.common import create_url_format, get_attachment_mimetype

from httpx import AsyncClient, HTTPStatusError

from aiofiles import open as asopen

from cachetools_async import cached  # pyright: ignore[reportUnknownVariableType]

from fbtools.official.utilities.global_instances import Cache


def _upload_messenger_attachment_key(
    _self: object, attachment: str, attachment_type: str, **_kwargs: Hashable
) -> str:
    return f"{attachment}-{attachment_type}"


class FacebookMessage:
    """FacebookMessage object."""

    def __init__(
        self,
        sender: str,
        recipient: str,
        text: str | None,
        message_id: str,
        attachments: list[Attachment],
        timestamp: int,
        session: AsyncClient,
        access_token: str,
        user_id: str | Literal["me"] = "me",
    ) -> None:
        """Initialize FacebookMessage.

        Args:
            sender: The sender id
            recipient: The recipient id
            text: The text of the message
            message_id: The message id
            attachments: The attachments of the message
            timestamp: The timestamp of the message
            session: The httpx async session object
            access_token: The page access token
            user_id: The user id or "me". The "me" is used on dev mode.

        """
        # important variables
        self._sender: str = sender
        self._recipient: str = recipient
        self._text: str | None = text
        self._message_id: str = message_id
        self._timestamp: int = timestamp
        self._attachments: list[Attachment] = attachments

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

    async def send_attachments(
        self,
        attachments: (
            str | FbMessageAttachment_Dict | list[str | FbMessageAttachment_Dict]
        ),
    ) -> "FacebookMessage":
        """Send an attachment to Facebook messenger.

        Supports multiple attachment types like images, video, audio and a file.

        Notes:
            There are certain limitations which each of the attachments like you can
            send multiple images at once but not on video, audio and a file.

        Args:
            attachments: The attachments of the message that can be url, local file, attachment id

        Returns:
            a FacebookMessage object.

        """
        attachment_data_list: list[dict[str, object]] = await self._manage_attachment(
            attachments=attachments
        )

        data: dict[str, object] = {"message": {"attachments": attachment_data_list}}

        if (
            len(attachment_data_list) == 1
            and attachment_data_list[0]["type"] != "image"
        ):
            attachment_data = attachment_data_list[0]

            data["message"] = {"attachment": attachment_data}

        else:
            # check if length is more than one and it has attachment type aside from image
            for attachment_data in attachment_data_list:
                if attachment_data["type"] != "image":
                    raise Exception(
                        "You can only send one attachment at a time on this kind of type: %s"
                        % attachment_data["type"]
                    )

        facebook_message_object = await self._send_api(data)
        return facebook_message_object

    async def send_image(
        self,
        attachments: (
            str | FbMessageAttachment_Dict | list[str | FbMessageAttachment_Dict]
        ),
    ) -> "FacebookMessage":
        """Send an image to Facebook messenger.

        You can send multiple images at once.

        Args:
            attachments: The attachments of the message that can be url, local file, attachment id

        Returns:
            a FacebookMessage object.

        """
        attachment_data_list: list[dict[str, object]] = await self._manage_attachment(
            attachments=attachments
        )

        data: dict[str, object] = {"message": {"attachments": attachment_data_list}}

        facebook_message_object = await self._send_api(data)
        return facebook_message_object

    async def send_audio(
        self, attachment: str | FbMessageAttachment_Dict
    ) -> "FacebookMessage":
        """Send an audio to Facebook messenger.

        You can only send one audio per request to the API.

        Args:
            attachment: The audio attachment that can be a url, local file, attachment id.

        Returns:
            a FacebookMessage object.

        """
        attachment_data_list = await self._manage_attachment(attachments=attachment)
        # we only need one
        attachment_data = attachment_data_list[0]

        data: dict[str, object] = {"message": {"attachment": attachment_data}}

        facebook_message_object = await self._send_api(data)
        return facebook_message_object

    async def send_video(
        self, attachment: str | FbMessageAttachment_Dict
    ) -> "FacebookMessage":
        """Send a video to Facebook messenger.

        You can only send one video per request to the API.

        Args:
            attachment: The video attachment that can be a url, local file, attachment id.

        Returns:
            a FacebookMessage object.

        """
        attachment_data_list = await self._manage_attachment(attachments=attachment)
        # we only need one
        attachment_data = attachment_data_list[0]

        data: dict[str, object] = {"message": {"attachment": attachment_data}}

        facebook_message_object = await self._send_api(data)
        return facebook_message_object

    async def send_file(
        self, attachment: str | FbMessageAttachment_Dict
    ) -> "FacebookMessage":
        """Send a file to Facebook messenger.

        You can only send one file per request to the API.

        Args:
            attachment: The file attachment that can be a url, local file, attachment id.

        Returns:
            a FacebookMessage object.

        """
        attachment_data_list = await self._manage_attachment(attachments=attachment)
        # we only need one
        attachment_data = attachment_data_list[0]

        data: dict[str, object] = {"message": {"attachment": attachment_data}}

        facebook_message_object = await self._send_api(data)
        return facebook_message_object

    async def send_quick_reply(
        self, text: str, quick_replies: list[QuickReplies_Dict]
    ) -> "FacebookMessage":
        """Send a quick reply to Facebook messenger.

        Args:
            text: Non-empty message text to send with the quick replies.
            quick_replies: List of quick replies data.

        Returns:
            a FacebookMessage object.

        """
        data: dict[str, object] = {
            "message": {"text": text, "quick_replies": quick_replies}
        }

        facebook_message_object = await self._send_api(data)
        return facebook_message_object

    async def send_generic_template(
        self, elements: list[GenericTemplate_Dict]
    ) -> "FacebookMessage":
        """Send a generic template to Facebook messenger.

        Args:
            elements: List of generic template data.

        Returns:
            a FacebookMessage object.

        """
        data: dict[str, object] = {
            "message": {
                "attachment": {
                    "type": "template",
                    "payload": {"template_type": "generic", "elements": elements},
                }
            }
        }

        facebook_message_object = await self._send_api(data)
        return facebook_message_object

    async def send_button_template(
        self,
        text: str,
        buttons: list[ButtonTemplateWeb_Dict | ButtonTemplatePostBack_Dict],
    ) -> "FacebookMessage":
        """Send a button template to Facebook messenger.

        Args:
            text: Non-empty message text to send with the quick replies.
            buttons: List of button data.

        Returns:
            a FacebookMessage object.

        """
        data: dict[str, object] = {
            "message": {
                "attachment": {
                    "type": "template",
                    "payload": {
                        "template_type": "button",
                        "text": text,
                        "buttons": buttons,
                    },
                }
            }
        }

        facebook_message_object = await self._send_api(data)
        return facebook_message_object

    async def send_media_template(
        self,
        attachment: str | FbMessageAttachment_Dict,
        buttons: list[ButtonTemplatePostBack_Dict | ButtonTemplateWeb_Dict],
    ) -> "FacebookMessage":
        """Send a media template to Facebook messenger.

        Notes:
            on attachment, url must be from Facebook url, like directly from your posts.

        Args:
            attachment: The media attachment that can be a facebook url, local file, attachment id.
            buttons: List of button data.

        Returns:
            a FacebookMessage object.

        """
        attachment_data = await self._manage_attachment(attachments=attachment)

        # since we only need one data being preprocessed
        attachment_data = attachment_data[0]

        # we know we are getting a dict of str on this one
        # so casting will just silence the linter
        media_type = cast(str, attachment_data["type"])
        payload = cast(dict[str, str], attachment_data["payload"])
        attachment_id = payload.get("attachment_id", None)
        attachment_url = payload.get("url", None)

        element_data: dict[
            str, str | list[ButtonTemplatePostBack_Dict | ButtonTemplateWeb_Dict]
        ] = {}
        element_data["media_type"] = media_type

        if attachment_id:
            element_data["attachment_id"] = attachment_id
        elif attachment_url:
            element_data["url"] = attachment_url
        else:
            raise Exception(
                "Attachment id or url is not found when sending media template."
            )

        element_data["buttons"] = buttons

        data: dict[str, object] = {
            "message": {
                "attachment": {
                    "type": "template",
                    "payload": {
                        "template_type": "media",
                        "elements": [element_data],
                    },
                }
            }
        }

        facebook_message_object = await self._send_api(data)
        return facebook_message_object

    # PROPERTY
    # ----------------------------------------
    @property
    def sender(self) -> str:
        """The `psid` of the sender."""
        return self._sender

    @property
    def recipient(self) -> str:
        """The `id` of the recipient."""
        return self._recipient

    @property
    def text(self) -> str | None:
        """The text of the message."""
        return self._text

    @property
    def message_id(self) -> str:
        """The message id of the message."""
        return self._message_id

    @property
    def timestamp(self) -> int:
        """The timestamp of the message."""
        return self._timestamp

    @property
    def attachments(self) -> list[Attachment]:
        """The attachments of the message."""
        return self._attachments

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

        try:
            facebook_message_response_object = FacebookMessageResponse.model_validate(
                response.json()
            )
        except ValidationError as _error:
            raise Exception("Failed to send message. from this error: " + response.text)

        # - sender is now recipient and recipient (the page) is now the sender
        facebook_message_object = FacebookMessage(
            sender=self._recipient,
            recipient=self._sender,
            text=self._text,
            attachments=self._attachments,
            # TODO: Do accurate timestamp, probably using datetime
            timestamp=self._timestamp,
            message_id=facebook_message_response_object.message_id,
            session=self._session,
            access_token=self._access_token,
            user_id=self._user_id,
        )

        return facebook_message_object

    async def _manage_attachment(
        self,
        attachments: (
            str | FbMessageAttachment_Dict | list[str | FbMessageAttachment_Dict]
        ),
    ) -> list[dict[str, object]]:
        """Centralize managing attachments.

        Notes:
            You can also send multiple attachments at once but for the image type
            only.

            You can only send send one audio, video and file per request to the API.

        Notes:
            When sending an attachment using the attachment id, you must use the
            dictionary format and you should provide the real mimetype of the
            attachment you are sending.

            Using attachment id is faster. It doesn't need an overhead of requesting
            for mimetype or uploading to facebook server.

        There are different type of attachment paramaters that you can use for
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
                attachment id and on local file because it needs to be uploaded
                on facebook server while the others need to check the mimetype.

                You can send an attachment url, filepath, attachment id or you don't know what type
                - use list of string or just a string.


        Notes:
            One error from the attachment provided will fail the rest. This to ensure that all
            attachments are sent properly and developers should be responsible for using a
            stable attachment source.

        Args:
            attachments: The attachments of the message that can be url, file, attachment id

        """
        attachment_data_list: list[dict[str, object]] = []

        if not isinstance(attachments, list):
            attachments = [attachments]

        for attachment in attachments:
            if isinstance(attachment, str):
                try:
                    attachment_type, mimetype = await get_attachment_mimetype(
                        attachment=attachment, session=self._session
                    )

                except HTTPStatusError as hse:
                    raise Exception(
                        "Something went wrong from requesting to image url header"
                        + f"\n{hse}"
                    )
                except Exception as exc:
                    raise Exception(
                        f"Invalid attachment source. Check if it is really a valid url or a valid local path. Reason:\n{exc}"
                    )
                if attachment.startswith("https://"):
                    attachment_data_list.append(
                        {
                            "type": attachment_type,
                            "payload": {"url": attachment},
                        }
                    )
                else:
                    if not attachment.isdigit():
                        # fix attachment type for file type because we don't know what kind of type the file type is
                        # with different mimetypes so they will be defaulted to "file"
                        if attachment_type not in ["image", "video", "audio"]:
                            attachment_type = "file"

                        # upload to facebook server to get the attachment id
                        attachment = await self._upload_messenger_attachment(
                            attachment=attachment,
                            attachment_type=attachment_type,
                            mimetype=mimetype,
                        )

                    attachment_data_list.append(
                        {
                            "type": attachment_type,
                            "payload": {"attachment_id": attachment},
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

                if attachment["source"].isdigit():
                    attachment_data_list.append(
                        {
                            "type": attachment["attachment_type"],
                            "payload": {"attachment_id": attachment["source"]},
                        }
                    )

                elif exists(attachment["source"]):
                    raise Exception(
                        "You should use the string method instead. Because handling a local file needs to be uploaded on facebook server."
                    )

                elif attachment["source"].startswith("https://"):
                    attachment_data_list.append(
                        {
                            "type": attachment["attachment_type"],
                            "payload": {
                                "url": attachment["source"],
                            },
                        }
                    )
                else:
                    raise Exception(
                        "Invalid attachment source. Check if it is really a valid url or a valid local path."
                    )

        return attachment_data_list

    @cached(cache=Cache.get_cache(), key=_upload_messenger_attachment_key)
    async def _upload_messenger_attachment(
        self,
        attachment: str,
        attachment_type: str,
        mimetype: str,
    ) -> str:
        """Upload the attachment to facebook server to get the attachment id.

        Notes:
            The attachment id that will generated from this API will expire in 90 days.
            This has been done to avoid uploading the same attachment over and over again.

            The attachment id generated from this API has different values than the main attachment id
            that was sent after getting the attachment id from this API.

            Basically [this_id_that_expires] -> [sent_to_messenger] -> [new_attachment_id_that_never_expires]

        Notes:
            You don't have to worry about the above notes, they are only an explanation how the attachment id works.

            The library itself will take care the problem of uploading the same attachment over and over again.

        """
        url = create_url_format(f"{self._user_id}/message_attachments")
        data: dict[str, object] = {
            "message": json.dumps(
                {
                    "attachment": {
                        "type": attachment_type,
                        "payload": {"is_reusable": True},
                    }
                }
            ),
            "type": mimetype,
        }
        params = {"access_token": self._access_token}

        # get local file data
        filename = basename(attachment)
        async with asopen(attachment, mode="rb") as f:
            files = {"filedata": (filename, await f.read(), mimetype)}

        # send to api
        response = await self._session.post(
            url=url, data=data, files=files, params=params
        )

        # we don't need pydantic to validate the data here since it is only
        # a one key dictionary, this is only to satisfy the linter
        response_data: dict[str, str] = cast(dict[str, str], response.json())

        if "attachment_id" not in response_data:
            raise Exception("Something went wrong when uploading the attachment.")

        return response_data["attachment_id"]
