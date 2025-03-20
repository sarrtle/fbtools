"""Post object.

This object will have full control of how you
handle a post.

Add post, edit post and delete post.
"""

from datetime import datetime, timezone
from typing import Literal

from httpx import AsyncClient


from fbtools.official.models.extra.facebook_post_attachment import (
    FacebookPostAttachment,
)
from fbtools.official.models.response.facebook_post_response import FacebookPostResponse
from fbtools.official.models.response.graph import SuccessResponse
from fbtools.official.utilities.common import create_url_format, raise_for_status
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
        access_token: str,
        session: AsyncClient,
    ):
        """Initialize FacebookPost.

        Args:
            post_id: The `id` of the post.
            access_token: The access token of the page.
            session: The httpx async session.

        """
        self._post_id: str = post_id
        self._message: str | None
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
        ) = None
        self._story: str | None = None
        self._attachments: list[FacebookPostAttachment] | None = None
        self._created_time: datetime = datetime.now(
            tz=timezone.utc
        )  # this is fine, will initialize them later
        self._access_token: str = access_token
        self._session: AsyncClient = session

        # inner attributes for request
        self._headers: dict[str, str] = {"Content-Type": "application/json"}

        # important attributes
        self._initialized: bool = False

    # =============== USEFUL METHODS ===============

    # ===== UPDATING POST =====
    async def update_post(
        self,
        message: str | None = None,
        attachments: list[str] | None = None,
    ) -> bool:
        """Update the post.

        Args:
            message: The new message written in the post.
            attachments: If you wish to add images/videos to the post.
            get_post_object: If you want to get the post object.

        Raises:
            ValidationError: If something went wrong during validation of api response.
            ValueError: If you did not provide either message or attachments.

        """
        if message is None and attachments is None:
            raise ValueError("You must provide either 'message' or 'attachments'.")

        url = create_url_format(self.post_id)
        data: dict[str, str | list[dict[str, str]]] = {}
        params = {"access_token": self._access_token}
        session = self._session

        if message:
            data["message"] = message

        if attachments:
            attached_media: list[dict[str, str]] = []

            for attachment in attachments:
                photo_id = await create_photo_id(
                    photo_url_or_path=attachment,
                    access_token=self._access_token,
                    session=session,
                )
                attached_media.append({"media_fbid": photo_id})

            data["attached_media"] = attached_media

        response = await session.post(
            url=url, json=data, params=params, headers=self._headers
        )
        raise_for_status(response)
        response_data: SuccessResponse = SuccessResponse.model_validate(response.json())

        # return boolean
        return response_data.success

    # ===== DELETING POST =====
    async def delete_post(self) -> bool:
        """Delete the post.

        Raises:
            HttpStatusError: If something went wrong during request.
            ValidationError: If something went wrong during validation of api response.

        """
        url = create_url_format(self.post_id)
        params = {"access_token": self._access_token}
        response = await self._session.delete(
            url=url, params=params, headers=self._headers
        )
        raise_for_status(response)
        response_data: SuccessResponse = SuccessResponse.model_validate(response.json())
        return response_data.success

    # ===== GETTING COMMENTS =====
    async def get_comments(self) -> "FacebookPost":
        """Get the comments of the post."""
        raise NotImplementedError

    # ===== GETTING LIKES =====
    async def get_likes(self) -> "FacebookPost":
        """Get the likes of the post."""
        raise NotImplementedError

    # ===== Initialize Properties =====
    async def initialize_properties(self) -> None:
        """Fetch post data from the Graph API and initialize its properties."""
        url = create_url_format(self.post_id)
        fields = [
            "id",
            "message",
            "status_type",
            "story",
            "created_time",
            "target",
            "attachments.limit(10){media,description,type,title,subattachments,unshimmed_url,target}",
        ]
        params = {"access_token": self._access_token, "fields": ",".join(fields)}
        response = await self._session.get(
            url=url, params=params, headers=self._headers
        )
        raise_for_status(response)
        response_object = FacebookPostResponse.model_validate(response.json())

        # check if the post is a bio
        is_bio = False

        # process attachments
        attachments: list[FacebookPostAttachment] = []
        if response_object.attachments:
            attachment_data = response_object.attachments.data[0]

            # for many multiple attachments
            if attachment_data.subattachments:
                for subattachments in attachment_data.subattachments.data:
                    # what I need
                    # attachment_id
                    attachment_id = subattachments.target.id
                    # src
                    # multiple videos and images has similar
                    # media properties `subattachment.media.image`

                    # if video
                    media_type = "video"
                    if (
                        subattachments.type == "video"
                        and subattachments.media.source != None
                    ):
                        src = subattachments.media.source

                    # if image
                    elif subattachments.type == "photo":
                        media_type = "image"
                        src = subattachments.media.image.src

                    else:
                        raise Exception(f"Unknown media type: {subattachments.type}")

                    # thumbnail_src
                    # since image doesn't have a thumbnail, the src
                    # is their real image but the video uses this as
                    # their thumbnail image
                    thumbnail_src = subattachments.media.image.src

                    # facebook_url
                    # The URL to facebook post that views the attachment.
                    facebook_url = subattachments.target.url

                    # description
                    description = subattachments.description

                    # height
                    subattachments.media.image.height
                    # width
                    subattachments.media.image.width

                    attachments.append(
                        FacebookPostAttachment(
                            attachment_id=attachment_id,
                            src=src,
                            thumbnail_src=thumbnail_src,
                            facebook_url=facebook_url,
                            description=description,
                            height=subattachments.media.image.height,
                            width=subattachments.media.image.width,
                            media_type=media_type,
                        )
                    )

            # if bio
            # bio uses attachments too
            elif attachment_data.type == "native_templates":
                is_bio = True
                # since bio don't have a message, it will use the
                # attachment description
                response_object.message = attachment_data.description

            # if single attachment
            else:

                assert (
                    attachment_data.media is not None
                ), "Attachment media is None on single attachment."

                attachment_id = attachment_data.target.id

                # if video
                media_type = "video"
                if (
                    attachment_data.type == "video_inline"
                    and attachment_data.media.source != None
                ):
                    src = attachment_data.media.source

                # if image
                elif attachment_data.type in ["photo", "album", "profile_media"]:
                    media_type = "image"
                    src = attachment_data.media.image.src
                else:
                    raise Exception(f"Unknown Attachment type {attachment_data.type}.")

                # if image_profile
                if attachment_data.type == "profile_media":
                    media_type = "image_profile"
                    response_object.status_type = "added_profile_photo"

                # if video reel
                if "reel" in attachment_data.target.url:
                    media_type = "video_reel"
                    response_object.status_type = "added_reel"

                # thumbnail_src
                # since image doesn't have a thumbnail, the src
                # is their real image but the video uses this as
                # their thumbnail image
                thumbnail_src = attachment_data.media.image.src

                # facebook_url
                # The URL to facebook post that views the attachment.
                facebook_url = attachment_data.target.url

                # description
                description = attachment_data.description

                attachments.append(
                    FacebookPostAttachment(
                        attachment_id=attachment_id,
                        src=src,
                        thumbnail_src=thumbnail_src,
                        facebook_url=facebook_url,
                        description=description,
                        height=attachment_data.media.image.height,
                        width=attachment_data.media.image.width,
                        media_type=media_type,
                    )
                )

        if is_bio:
            response_object.status_type = "bio_status_update"

        # add them to their attributes
        self._message = response_object.message
        self._status_type = response_object.status_type
        self._story = response_object.story
        self._created_time = response_object.created_time
        self._attachments = attachments or None
        self._initialized = True

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
        "_initialized",
    }

    # ========== ATTRIBUTE PROPERTIES ==========

    @property
    def post_id(self) -> str:
        """The `id` of the post."""
        return self._post_id

    @property
    def message(self) -> str | None:
        """Message written on the post."""
        self._check_initialized()
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
        """Description of the type of a status update."""
        self._check_initialized()
        return self._status_type

    @property
    def story(self) -> str | None:
        """Auto-generated stories (e.g., friend connections)."""
        self._check_initialized()
        return self._story

    @property
    def attachments(self) -> list[FacebookPostAttachment] | None:
        """The attachments of the post."""
        self._check_initialized()
        return self._attachments

    @property
    def created_time(self) -> datetime:
        """The time the post was published, expressed as UNIX timestamp."""
        self._check_initialized()
        return self._created_time

    # ========== PRIVATE METHODS AND CLASS METHODS ==========
    def _check_initialized(self):
        """Check if properties are initialized."""
        if not self._initialized:
            raise Exception(
                "Properties were not initialized. Consider calling `FacebookPost.initialize_properties()` first."
            )
