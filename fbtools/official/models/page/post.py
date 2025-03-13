"""Post object.

This object will have full control of how you
handle a post.

Add post, edit post and delete post.
"""

from datetime import datetime
from typing import Literal

from httpx import AsyncClient


from fbtools.official.models.extra.attachments import Attachment
from fbtools.official.models.response.graph import SuccessResponse
from fbtools.official.utilities.common import create_url_format
from fbtools.official.utilities.graph_util import (
    create_photo_id,
)


class FacebookPost:
    """Facebook post object.

    Base object for post data. Easily navigate and use
    the post object.

    Notes:
        Some methods are separated from the attributes as they
        need extra https request to get their data.

    """

    def __init__(
        self,
        post_id: str,
        message: str | None,
        status_type: (
            Literal[
                "added_photos",
                "added_video",
                "added_reel",
                "added_profile_photo",
                "mobile_status_update",
                "bio_status_update",
            ]
            | None
        ),
        story: str | None,
        attachments: list[Attachment] | None,
        created_time: datetime,
        access_token: str,
        session: AsyncClient,
    ):
        """Initialize FacebookPost.

        Args:
            post_id: The `id` of the post.
            message: Message written in the post.
            status_type: Description of the type of a status update.
            story: Auto-generated stories (e.g., friend connections).
            created_time: The time the post was published, expressed as UNIX timestamp
            attachments: The attachments of the post.
            access_token: The access token of the page.
            session: The httpx async session.

        """
        self._post_id: str = post_id
        self._message: str | None = message
        self._status_type: (
            Literal[
                "added_photos",
                "added_video",
                "added_reel",
                "added_profile_photo",
                "mobile_status_update",
                "bio_status_update",
            ]
            | None
        ) = status_type
        self._story: str | None = story
        self._attachments: list[Attachment] | None = attachments
        self._created_time: datetime = created_time
        self._access_token: str = access_token
        self._session: AsyncClient = session

        # inner attributes for request
        self._headers: dict[str, str] = {"Content-Type": "application/json"}

    # =============== USEFUL METHODS ===============

    # ===== UPDATING POST =====
    async def update_post(
        self,
        message: str,
        attachments: list[str] | None = None,
    ) -> bool:
        """Update the post.

        Args:
            message: The new message written in the post.
            attachments: If you wish to add images/videos to the post.
            get_post_object: If you want to get the post object.

        Raise:
            ValidationError: If something went wrong during validation of api response.

        """
        url = create_url_format(self.post_id)
        data = {"message": message}
        params = {"access_token": self._access_token}
        session = self._session

        if attachments:
            attached_media: list[dict[str, str]] = []

            for attachment in attachments:
                photo_id = await create_photo_id(
                    photo_url_or_path=attachment,
                    access_token=self._access_token,
                    session=session,
                )
                attached_media.append({"media_fbid": photo_id})

        response = await session.post(
            url=url, json=data, params=params, headers=self._headers
        )
        response_data: SuccessResponse = SuccessResponse.model_validate(response.json())

        # return boolean
        return response_data.success

    # ===== DELETING POST =====
    async def delete_post(self) -> "FacebookPost":
        """Delete the post."""
        raise NotImplementedError

    # ===== GETTING COMMENTS =====
    async def get_comments(self) -> "FacebookPost":
        """Get the comments of the post."""
        raise NotImplementedError

    # ===== GETTING LIKES =====
    async def get_likes(self) -> "FacebookPost":
        """Get the likes of the post."""
        raise NotImplementedError

    # =============== OBJECT CONTROL ===============
    __slots__: set[str] = {
        "_post_id",
        "_message",
        "_status_type",
        "_story",
        "_attachments",
        "_created_time",
        "_access_token",
        "_session",
        "_headers",
        "_url",
    }

    @property
    def post_id(self) -> str:
        """Get the post id."""
        return self._post_id

    @property
    def message(self) -> str | None:
        """Get the message of the post."""
        return self._message

    @property
    def status_type(
        self,
    ) -> (
        Literal[
            "added_photos",
            "added_video",
            "added_reel",
            "added_profile_photo",
            "mobile_status_update",
            "bio_status_update",
        ]
        | None
    ):
        """Get the status type of the post."""
        return self._status_type

    @property
    def story(self) -> str | None:
        """Get the story of the post."""
        return self._story

    @property
    def attachments(self) -> list[Attachment] | None:
        """Get the attachments of the post."""
        return self._attachments

    @property
    def created_time(self) -> datetime:
        """Get the created time of the post."""
        return self._created_time
