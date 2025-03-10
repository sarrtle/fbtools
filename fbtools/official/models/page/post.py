"""Post object.

This object will have full control of how you
handle a post.

Add post, edit post and delete post.
"""

from datetime import datetime
from typing import Literal, overload


from fbtools.official.models.response.graph import SuccessResponse
from fbtools.official.page import Page
from fbtools.official.utilities.common import create_url_format


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
        status_type: Literal["added_photos", "added_video", "mobile_status_update"],
        story: str | None,
        created_time: datetime,
        page_object: Page,
    ):
        """Initialize FacebookPost.

        Args:
            post_id: The `id` of the post.
            message: Message written in the post.
            status_type: Description of the type of a status update.
            story: Auto-generated stories (e.g., friend connections).
            created_time: The time the post was published, expressed as UNIX timestamp
            page_object: The Page object

        """
        self._post_id: str = post_id
        self._message: str | None = message
        self._status_type: Literal[
            "added_photos", "added_video", "mobile_status_update"
        ] = status_type
        self._story: str | None = story
        self._created_time: datetime = created_time
        self._page_object: Page = page_object

        # inner attributes for request
        self._headers: dict[str, str] = {"Content-Type": "application/json"}

    # =============== USEFUL METHODS ===============

    # ===== UPDATING POST =====
    @overload
    async def update_post(
        self,
        message: str,
        attachments: list[str] | None = None,
        get_post_object: bool = True,
    ) -> "FacebookPost": ...

    @overload
    async def update_post(
        self,
        message: str,
        attachments: list[str] | None = None,
        get_post_object: bool = False,
    ) -> bool: ...

    async def update_post(
        self,
        message: str,
        attachments: list[str] | None = None,
        get_post_object: bool = False,
    ) -> "FacebookPost | bool":
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
        params = {"access_token": self._page_object.access_token}
        session = self._page_object.session

        if attachments:
            attached_media: list[dict[str, str]] = []

            for attachment in attachments:
                photo_id = await self._page_object.create_photo_id(
                    photo_url_or_path=attachment
                )
                attached_media.append({"media_fbid": photo_id})

        response = await session.post(
            url=url, json=data, params=params, headers=self._headers
        )
        response_data: SuccessResponse = SuccessResponse.model_validate(response.json())

        # Get as post object
        if get_post_object:
            return await self._page_object.get_post_object(post_id=self.post_id)

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
        "_created_time",
        "_page_object",
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
    ) -> Literal["added_photos", "added_video", "mobile_status_update"]:
        """Get the status type of the post."""
        return self._status_type

    @property
    def story(self) -> str | None:
        """Get the story of the post."""
        return self._story

    @property
    def created_time(self) -> datetime:
        """Get the created time of the post."""
        return self._created_time
