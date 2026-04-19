"""Post node of Facebook Graph API."""

from pathlib import Path
from httpx import AsyncClient

from fbtools.models.page.feed_post_upload import AttachedMedia, FeedPostUploadData
from fbtools.models.page.id_response import IdResponse
from fbtools.models.utilities.bool_response import BoolResponse
from fbtools.utilities.common import is_url_valid, raise_for_status
from fbtools.utilities.core import create_photo_id


class FacebookPost:
    """Post node of Facebook Graph API."""

    def __init__(self, post_id: str, access_token: str, session: AsyncClient):
        """Initialize Facebook Post.

        Args:
            post_id: Post ID.
            access_token: Page access token.
            session: Async Httpx Session.

        """
        # private attributes
        self._post_id: str = post_id
        self._access_token: str = access_token
        self._session: AsyncClient = session

    async def edit(
        self, message: str | None = None, attachments: str | list[str] | None = None
    ) -> bool:
        """Edit facebook post.

        Notes:
            editing video post is not yet tested and I think it has a different process.

        Args:
            message: The message written in the post.
            attachments: If you wished to add attachments to the post.

        """
        data = FeedPostUploadData(message=message)
        # no need publish here since it is already published
        data.published = False

        if attachments:
            if isinstance(attachments, str):
                attachments = [attachments]

            data.attached_media = []

            for attachment in attachments:
                # TODO: Needs further optimization if many attachment images
                #       will be uploaded.
                photo_id = await create_photo_id(
                    photo_url_or_file_path=attachment,
                    access_token=self._access_token,
                    session=self._session,
                )
                data.attached_media.append(AttachedMedia(media_fbid=photo_id))

        params = {"access_token": self._access_token}
        response = await self._session.post(
            self._post_id, json=data.model_dump(), params=params
        )
        raise_for_status(response=response)

        bool_response = BoolResponse.model_validate(response.json())

        return bool_response.success

    async def delete(self) -> bool:
        """Delete facebook post."""
        params = {"access_token": self._access_token}
        response = await self._session.delete(self._post_id, params=params)
        raise_for_status(response=response)
        response_data = BoolResponse.model_validate(response.json())
        return response_data.success

    async def add_comment(self, message: str, attachment: str | None = None) -> str:
        """Add comment to facebook post.

        Notes:
            Temporary solution to add comment without the comment object
            from the old fbtools-backup.

        Args:
            message: The message written in the comment.
            attachment: If you wished to add attachments to the comment.

        """
        url = f"{self._post_id}/comments"
        params = {"access_token": self._access_token}
        data: dict[str, str | None] = {}

        if message:
            data["message"] = message

        if attachment:
            if is_url_valid(attachment):
                data["attachment_url"] = attachment

            elif Path(attachment).is_file():
                photo_id = await create_photo_id(
                    photo_url_or_file_path=attachment,
                    access_token=self._access_token,
                    session=self._session,
                )
                data["attachment_id"] = photo_id
            else:
                raise ValueError(
                    f"Invalid attachment: {attachment}. Please ensure you provided a valid URL or file path."
                )

        response = await self._session.post(url, json=data, params=params)
        raise_for_status(response=response)

        response_data = IdResponse.model_validate(response.json())

        return response_data.id
