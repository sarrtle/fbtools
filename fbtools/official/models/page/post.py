"""Post object.

This object will have full control of how you
handle a post.

Add post, edit post and delete post.
"""

from datetime import datetime, timezone
from typing import Literal, cast, override
import json

from httpx import AsyncClient
from pydantic import TypeAdapter

import fbtools.official.models.page.comment as fb_comment
from fbtools.official.models.extra.facebook_post_attachment import (
    FacebookPostAttachment,
)
from fbtools.official.models.response.facebook_post_response import (
    AllCommentCount,
    BatchResponseForCommentCount,
    BatchResponseForPost,
    FacebookPostResponse,
)
from fbtools.official.models.response.graph import SuccessResponse
from fbtools.official.utilities.common import (
    create_comment_fields,
    create_url_format,
    raise_for_status,
)
from fbtools.official.utilities.graph_util import (
    create_photo_id,
)

# Types for initializing object
BATCH_RESPONSE = TypeAdapter(list[BatchResponseForPost | BatchResponseForCommentCount])


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
            get_comments: If you want to get the comments of the post.

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
        self._attachments: list[FacebookPostAttachment] = []
        self._created_time: datetime = datetime.now(
            tz=timezone.utc
        )  # this is fine, will initialize them later
        self._reaction_count: int = 0
        self._page_reaction: (
            Literal["LIKE", "LOVE", "CARE", "HAHA", "WOW", "SAD", "ANGRY"] | None
        ) = None
        self._comments: list[fb_comment.FacebookComment] = []
        self._can_comment: bool = False
        self._are_comments_available: bool = False
        self._available_comments_count: int = 0
        self._comments_count: int = 0
        self._shares_count: int = 0

        self._access_token: str = access_token
        self._session: AsyncClient = session

        # inner attributes for request
        self._headers: dict[str, str] = {"Content-Type": "application/json"}

        # important attributes
        self._initialized: bool = False

    # ===============================================
    #               USEFUL METHODS
    # ===============================================
    async def edit_post(
        self,
        message: str | None = None,
        attachments: list[str] | None = None,
    ) -> bool:
        """Edit the post.

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

        if message != None:
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

    async def get_comments(self) -> "FacebookPost":
        """Get the comments of the post.

        Will append the comments to the comments attribute.
        """
        raise NotImplementedError

    async def get_likes(self) -> "FacebookPost":
        """Get the likes of the post."""
        raise NotImplementedError

    async def refresh(self) -> None:
        """Refresh the post object.

        Warning:
            Doing this will reset the post object.

        """
        await self.initialize_properties()

    async def initialize_properties(self, get_comments: bool = False) -> None:
        """Fetch post data from the Graph API and initialize its properties.

        The `get_comments` is separated because you might not want to get comments if
        you just want to use the post object for something else. This will save you
        bytes from your apps.

        Args:
            get_comments: If you want to get the comments of the post.

        """
        url = create_url_format(self.post_id)
        fields = [
            "id",
            "message",
            "status_type",
            "story",
            "created_time",
            "target",
            "attachments.limit(10){media,description,type,title,subattachments,unshimmed_url,target}",
            "reactions.summary(true)",
            "shares",
        ]

        # additional params for comments
        if get_comments:
            fields.append("comments.summary(true){%s}" % create_comment_fields())

        # create fields
        request_field = ", ".join(fields)

        # batch request data
        batch_request_data = json.dumps(
            [
                {
                    "method": "GET",
                    "relative_url": "%s?fields=%s" % (self.post_id, request_field),
                },
                {
                    "method": "GET",
                    "relative_url": "%s/comments?summary=true&filter=stream&limit=0"
                    % self.post_id,
                },
            ]
        )
        params = {
            "access_token": self._access_token,
            "batch": batch_request_data,
            "include_headers": "false",
        }
        response = await self._session.post(
            url=url, params=params, headers=self._headers
        )

        raise_for_status(response)

        facebook_post: FacebookPostResponse | None = None
        facebook_comment_all_count: AllCommentCount | None = None

        raw_data = cast(list[dict[str, object]], response.json())
        response_object = BATCH_RESPONSE.validate_python(raw_data)

        # put the data to their respective variables
        for rd in response_object:
            # check response status
            if rd.code != 200:
                raise Exception(rd.body)

            if isinstance(rd, BatchResponseForPost):
                facebook_post = rd.body
            else:
                facebook_comment_all_count = rd.body

        # all these exceptions will be one exception object for
        # initialization error with these kind of messages
        if facebook_post == None:
            raise Exception("Post response was not found")

        if facebook_comment_all_count == None:
            raise Exception("Comment count count was not found")

        # check if the post is a bio
        is_bio = False

        # process attachments
        attachments: list[FacebookPostAttachment] = []
        if facebook_post.attachments:
            attachment_data = facebook_post.attachments.data[0]

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
                facebook_post.message = attachment_data.description

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
                    facebook_post.status_type = "added_profile_photo"

                # if video reel
                if "reel" in attachment_data.target.url:
                    media_type = "video_reel"
                    facebook_post.status_type = "added_reel"

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
            facebook_post.status_type = "bio_status_update"

        # process comments
        if facebook_post.comments:
            for comment in facebook_post.comments.data:
                comment_object = fb_comment.FacebookComment(
                    comment_id=comment.id,
                    access_token=self._access_token,
                    session=self._session,
                    parent_comment=None,
                    parent_post=self,
                )
                comment_object.put_initialized_properties(comment)

                # print(len(cdt))

                self._comments.append(comment_object)

        # comment count
        self._comments_count = facebook_comment_all_count.summary.total_count

        # reaction count
        if facebook_post.reactions:
            self._reaction_count = facebook_post.reactions.summary.total_count

        # page reaction
        if facebook_post.reactions:
            self._page_reaction = facebook_post.reactions.summary.viewer_reaction

        # share count
        if facebook_post.shares:
            self._shares_count = facebook_post.shares.count

        # indicator
        self._can_comment = facebook_comment_all_count.summary.can_comment

        # add them to their attributes
        self._message = facebook_post.message
        self._status_type = facebook_post.status_type
        self._story = facebook_post.story
        self._created_time = facebook_post.created_time
        self._attachments = attachments
        self._initialized = True

    # ===============================================
    #               OBJECT CONTROL
    # ===============================================
    __slots__: set[str] = {
        "_post_id",
        "_message",
        "_status_type",
        "_story",
        "_attachments",
        "_created_time",
        "_reaction_count",
        "_page_reaction",
        "_comments",
        "_can_comment",
        "_comment_count",
        "_are_comments_available",
        "_available_comments_count",
        "_comments_count",
        "_shares_count",
        "_access_token",
        "_session",
        "_headers",
        "_url",
        "_initialized",
    }

    @override
    def __repr__(self) -> str:
        return (
            f"FacebookPost("
            f"post_id={self._post_id}, "
            f"message={self._message}, "
            f"status_type={self._status_type}, "
            f"story={self._story}, "
            f"attachments={len(self._attachments)}, "
            f"comments={len(self._comments)}, "
            f"created_time={self._created_time}, "
            f"initialized={self._initialized}"
            f")"
        )

    # ===============================================
    #           ATTRIBUTE PROPERTIES
    # ===============================================
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
    def attachments(self) -> list[FacebookPostAttachment]:
        """The attachments of the post."""
        self._check_initialized()
        return self._attachments

    @property
    def created_time(self) -> datetime:
        """The time the post was published, expressed as UNIX timestamp."""
        self._check_initialized()
        return self._created_time

    @property
    def reaction_count(self) -> int:
        """The number of reactions to the post."""
        self._check_initialized()
        return self._reaction_count

    @property
    def is_page_reacted(self) -> bool:
        """Whether the page reacted to the post."""
        self._check_initialized()
        return self._page_reaction is not None

    @property
    def page_reaction(
        self,
    ) -> Literal["LIKE", "LOVE", "CARE", "HAHA", "WOW", "SAD", "ANGRY"] | None:
        """The reaction of the page to the post.

        Raises:
            Exception: If the page has not reacted to the post.

        """
        self._check_initialized()
        return self._page_reaction

    @property
    def comments(self) -> list["fb_comment.FacebookComment"]:
        """The comments on the post."""
        self._check_initialized()
        return self._comments

    @property
    def can_comment(self) -> bool:
        """Whether the post can be commented on."""
        self._check_initialized()
        return self._can_comment

    @property
    def comments_count(self) -> int:
        """The number of comments on the post."""
        self._check_initialized()
        return self._comments_count

    @property
    def shares_count(self) -> int:
        """The number of shares on the post."""
        self._check_initialized()
        return self._shares_count

    # ===============================================
    #           PRIVATE METHODS
    # ===============================================
    def _check_initialized(self):
        """Check if properties are initialized.

        Raises:
            Exception: Properties were not initialized.

        """
        if not self._initialized:
            raise Exception(
                "Properties were not initialized. Consider calling `FacebookPost.initialize_properties()` first."
            )
