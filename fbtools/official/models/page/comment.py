"""Comment object.

This object will have full control of how you
handle a comment.

Add comment, edit comment and delete comment.
"""

from datetime import datetime
from typing import Literal, override
from os.path import exists
from httpx import AsyncClient

from fbtools.official.models.extra.facebook_comment_models import (
    FacebookCommentAuthor,
    FacebookCommentAttachment,
)
from fbtools.official.models.response.facebook_comment_response import (
    CommentData,
    FacebookCommentResponse,
)
from fbtools.official.models.response.graph import SuccessResponse
from fbtools.official.utilities.common import create_url_format, raise_for_status
from fbtools.official.utilities.graph_util import create_photo_id


class FacebookComment:
    """Facebook comment object.

    Base object for comment data. Easily navigate and use
    the comment object.

    Notes:
        If you are receiving comment object from listening event,
        you need to initialize the data. Otherwise, you don't need
        to as the comment data are already given from other requests
        such as getting comments from post, and getting reply from the
        comments.

    Notes:
        If there is a comment reply in this comment object, they
        will be limited upto 10 comment reply only. Otherwise, to
        get all of the comment reply, you need to use the `get_reply_comments`
        method.

    """

    def __init__(self, comment_id: str, access_token: str, session: AsyncClient):
        """Initialize FacebookComment.

        Args:
            comment_id: the `id` of the comment.
            access_token: The access token of the page
            session: The httpx async session

        """
        self._comment_id: str = comment_id
        self._access_token: str = access_token
        self._session: AsyncClient = session

        # initialize attributes that is not their data
        self._message: str | None = None
        self._reaction_count: int = 0
        self._page_reaction: (
            Literal["LIKE", "LOVE", "CARE", "HAHA", "WOW", "SAD", "ANGRY"] | None
        ) = None
        self._replies: list[FacebookComment] = []
        self._author: FacebookCommentAuthor | None = None
        self._attachment: FacebookCommentAttachment | None = None
        self._created_time: datetime = datetime.now()
        self._are_replies_available: bool = False
        self._available_reply_count: int = 0

        self._headers: dict[str, str] = {"Content-Type": "application/json"}
        self._initilized: bool = False
        self._current_reply_after_cursor: str | None = None

    # ===============================================
    #               USEFUL METHODS
    # ===============================================
    async def update_comment(self, message: str, attachment: str | None = None) -> bool:
        """Update the comment.

        Message is required since it will be removed when you only update
        the attachment without the message.

        Args:
            message: The new message written in the comment.
            attachment: If you wish to add images/videos to the comment.

        Raises:
            ValidationError: If something went wrong during validation of api response.
            ValueError: If you did not provide either message or attachment.

        """
        url = create_url_format(self.comment_id)
        data: dict[str, str | list[dict[str, str]]] = {}
        params = {"access_token": self._access_token}
        session = self._session

        data["message"] = message

        if attachment:
            if attachment.startswith("https://"):
                data["attachment_url"] = attachment
            elif exists(attachment):
                photo_id = await create_photo_id(
                    photo_url_or_path=attachment,
                    access_token=self._access_token,
                    session=session,
                )
                data["attachment_id"] = photo_id
            else:
                raise ValueError(
                    "Can't validate your attachment. Please ensure you provided a valid url or file path."
                )

        response = await session.post(
            url=url, params=params, headers=self._headers, json=data
        )
        raise_for_status(response)
        response_data: SuccessResponse = SuccessResponse.model_validate(response.json())

        return response_data.success

    async def delete_comment(self) -> bool:
        """Delete the comment.

        Raises:
            HttpStatusError: If something went wrong during request.
            ValidationError: If something went wrong during validation of api response.

        """
        url = create_url_format(self.comment_id)
        params = {"access_token": self._access_token}
        response = await self._session.delete(
            url=url, params=params, headers=self._headers
        )
        raise_for_status(response)
        response_data: SuccessResponse = SuccessResponse.model_validate(response.json())
        return response_data.success

    async def get_reply_comments(
        self, limit: int | None = None
    ) -> list["FacebookComment"]:
        """Get the reply comments of the comment.

        Args:
            limit: The maximum number of reply comments to return.

        Raises:
            ValidationError: If something went wrong during validation of api response.
            HttpStatusError: If something went wrong during request.

        Returns:
            A list of reply comments.

        """
        # early catch if no reply available
        if not self.are_replies_available:
            raise Exception("No replies available")

        reply_comments: list[FacebookComment] = []

        url = create_url_format(f"{self.comment_id}/comments")
        params = self._create_params()
        next = True

        # apply the current after cursor if it exists
        # so we will immediately get the next reply comments
        # instead of existing ones
        if self._current_reply_after_cursor:
            params["after"] = self._current_reply_after_cursor

        # apply limit
        if limit != None:
            params["limit"] = str(limit)

        # set summary on this endpoint only
        params["summary"] = "true"

        while next == True and len(reply_comments) < limit if limit else True:
            response = await self._session.get(
                url=url, params=params, headers=self._headers
            )
            raise_for_status(response)
            response_object: CommentData = CommentData.model_validate(response.json())

            for reply_comment in response_object.data:
                reply_comment_object = FacebookComment(
                    comment_id=reply_comment.id,
                    access_token=self._access_token,
                    session=self._session,
                )
                reply_comment_object.put_initialized_properties(
                    response_object=reply_comment
                )
                reply_comments.append(reply_comment_object)

            # Note: not using the paging.next url because they don't retain
            #       the same parameters
            if response_object.paging:
                self._current_reply_after_cursor = response_object.paging.cursors.after
                params["after"] = self._current_reply_after_cursor
                next = response_object.paging.next is not None
            else:
                next = False

            if limit == None and next == False:
                break

        # new reply comments will automatically put
        # in the original comment object replies
        self._replies.extend(reply_comments)

        # update reply data
        self._available_reply_count = self._available_reply_count - len(reply_comments)
        self._are_replies_available = self._available_reply_count > 0

        # returning the current requested reply comments for
        # other uses
        return reply_comments[:limit] if limit else reply_comments

    async def initialize_properties(self) -> None:
        """Fetch comment data from the Graph API and initialize properties."""
        url = create_url_format(self.comment_id)
        params = self._create_params()
        response = await self._session.get(
            url=url, params=params, headers=self._headers
        )

        raise_for_status(response)

        response_object: FacebookCommentResponse = (
            FacebookCommentResponse.model_validate(response.json())
        )

        self._parse_response_object(response_object)

    def put_initialized_properties(
        self, response_object: FacebookCommentResponse
    ) -> None:
        """Register properties that were initialized outside the object.

        This occurs because some data already contains comment information.
        Initializing these properties for each comment object individually
        would be inefficient and result in excessive API requests.
        """
        self._parse_response_object(response_object)

    # ===============================================
    #               OBJECT CONTROL
    # ===============================================
    __slots__: set[str] = {
        "_comment_id",
        "_message",
        "_access_token",
        "_session",
        "_reaction_count",
        "_is_page_reacted",
        "_page_reaction",
        "_replies",
        "_author",
        "_attachment",
        "_created_time",
        "_are_replies_available",
        "_available_reply_count",
        "_headers",
        "_initilized",
        "_current_reply_after_cursor",
    }

    @override
    def __repr__(self) -> str:
        return (
            f"FacebookComment("
            f"comment_id={self._comment_id}, "
            f"message={self._message}, "
            f"reaction_count={self._reaction_count}, "
            f"is_page_reacted={self.is_page_reacted}, "
            f"page_reaction={self._page_reaction}, "
            f"replies={self._replies}, "
            f"author={self._author}, "
            f"attachment={self._attachment}, "
            f"created_time={self._created_time}, "
            f"initialized={self.is_initialized}"
            f")"
        )

    # ===============================================
    #           ATTRIBUTE PROPERTIES
    # ===============================================
    @property
    def comment_id(self) -> str:
        """The `id` of the comment."""
        return self._comment_id

    @property
    def message(self) -> str | None:
        """The `message` of the comment."""
        self._is_initialized()
        return self._message

    @property
    def reaction_count(self) -> int:
        """The `like_count` of the comment."""
        self._is_initialized()
        return self._reaction_count

    @property
    def is_page_reacted(self) -> bool:
        """Whether the page reacted to the comment."""
        self._is_initialized()
        return self._page_reaction is not None

    @property
    def page_reaction(
        self,
    ) -> Literal["LIKE", "LOVE", "CARE", "HAHA", "WOW", "SAD", "ANGRY"] | None:
        """The reaction of the page to the comment.

        Raises:
            Exception: If the page has not reacted to the comment.

        """
        self._is_initialized()
        return self._page_reaction

    @property
    def replies(self) -> list["FacebookComment"]:
        """The replies of the comment."""
        self._is_initialized()
        return self._replies

    @property
    def author(self) -> FacebookCommentAuthor | None:
        """The author of the comment."""
        self._is_initialized()
        return self._author

    @property
    def attachment(self) -> FacebookCommentAttachment | None:
        """The attachments of the comment."""
        self._is_initialized()
        return self._attachment

    @property
    def created_time(self) -> datetime:
        """The `created_time` of the comment."""
        self._is_initialized()
        return self._created_time

    @property
    def are_replies_available(self) -> bool:
        """Whether the replies of the comment are available."""
        self._is_initialized()
        return self._are_replies_available

    @property
    def available_reply_count(self) -> int:
        """The number of available replies of the comment."""
        self._is_initialized()
        return self._available_reply_count

    @property
    def is_initialized(self) -> bool:
        """Whether the comment object is initialized."""
        return self._initilized

    # ===============================================
    #           PRIVATE METHODS
    # ===============================================
    def _create_params(self) -> dict[str, str]:
        """Create the parameters for the Graph API request."""
        comment_fields = [
            "attachment",
            "created_time",
            "from",
            "id",
            "like_count",
            "message",
            "parent",
            "user_likes",
            "reactions.summary(true)",
            "permalink_url",
            "object",
            "comments.summary(true)",
            "likes",
        ]

        reaction_fields = [
            "id",
            "name",
            "type",
            "username",
            "profile_type",
            "pic_large",
            "pic_small",
            "link",
            "can_post",
        ]

        # add reaction fields on the comment
        comment_fields[
            comment_fields.index("reactions.summary(true)")
        ] += "{%s}" % ",".join(reaction_fields)

        # add comment fields on the comment
        comment_fields[
            comment_fields.index("comments.summary(true)")
        ] += "{%s}" % ",".join(comment_fields)

        params = {
            "access_token": self._access_token,
            "fields": "%s" % ",".join(comment_fields),
        }
        return params

    def _is_initialized(self) -> None:
        """Initialize the comment object."""
        if not self._initilized:
            raise Exception("Comment object is not initialized.")

    def _parse_response_object(self, response_object: FacebookCommentResponse):
        """Parse the response object and initialize the comment object."""
        # comment message
        self._message = response_object.message

        # created time
        self._created_time = response_object.created_time

        # comment author
        if response_object.from_ != None:
            self._author = FacebookCommentAuthor(
                id=response_object.from_.id, name=response_object.from_.name
            )

        # comment id
        self._comment_id = response_object.id

        # attachments
        if response_object.attachment != None:
            attachment_id = response_object.attachment.target.id

            match response_object.attachment.type:
                case "photo":
                    media_type = "image"
                case "video_inline":
                    media_type = "video"
                case "animated_image_share":
                    media_type = "gif"

            if response_object.attachment.media.source != None:
                src = response_object.attachment.media.source
            else:
                src = response_object.attachment.media.image.src

            thumbnail_src = response_object.attachment.media.image.src

            facebook_url = response_object.attachment.target.url

            height = response_object.attachment.media.image.height
            width = response_object.attachment.media.image.width

            self._attachment = FacebookCommentAttachment(
                attachment_id=attachment_id,
                src=src,
                thumbnail_src=thumbnail_src,
                facebook_url=facebook_url,
                height=height,
                width=width,
                media_type=media_type,
            )

        # like count
        self._reaction_count = response_object.reactions.summary.total_count

        # page reaction
        self._page_reaction = response_object.reactions.summary.viewer_reaction

        # comment replies
        if response_object.comments != None:
            for comment in response_object.comments.data:
                reply_comment_object = FacebookComment(
                    comment_id=self.comment_id,
                    access_token=self._access_token,
                    session=self._session,
                )
                reply_comment_object.put_initialized_properties(response_object=comment)

                self._replies.append(reply_comment_object)

            # available reply count
            self._available_reply_count = (
                response_object.comments.summary.total_count - len(self._replies)
            )

            # are replies available
            self._are_replies_available = self._available_reply_count > 0

            if response_object.comments.paging and self._are_replies_available:
                self._current_reply_after_cursor = (
                    response_object.comments.paging.cursors.after
                )

        # set as initialized
        self._initilized = True
