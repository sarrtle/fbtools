"""Comment object.

This object will have full control of how you
handle a comment.

Add comment, edit comment and delete comment.
"""

# remove warning as it is already solved by importing
# the parent module instead of importing the object
# this will only affect the file, not globally
# pyright: reportImportCycles=false

import asyncio
from datetime import datetime
from typing import Literal, override
from os.path import exists
import warnings
from httpx import AsyncClient

import fbtools.official.models.page.post as fb_post

from fbtools.official.models.extra.facebook_comment_models import (
    FacebookCommentAuthor,
    FacebookCommentAttachment,
)
from fbtools.official.models.response.facebook_comment_response import (
    CommentAttachment,
    CommentData,
    FacebookCommentResponse,
)
from fbtools.official.models.response.graph import ObjectIdResponse, SuccessResponse
from fbtools.official.utilities.common import (
    create_comment_fields,
    create_url_format,
    raise_for_status,
)
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
        will be limited upto 25 comment reply only. Otherwise, to
        get all of the comment reply, you need to use the `get_reply_comments`
        method.

    """

    def __init__(
        self,
        comment_id: str,
        access_token: str,
        session: AsyncClient,
        parent_comment: "FacebookComment | None" = None,
        parent_post: "fb_post.FacebookPost | None" = None,
    ):
        """Initialize FacebookComment.

        Args:
            comment_id: the `id` of the comment.
            access_token: The access token of the page
            session: The httpx async session
            parent_comment: The parent comment
            parent_post: The parent post

        """
        self._comment_id: str = comment_id
        self._access_token: str = access_token
        self._session: AsyncClient = session
        self._parent_comment: FacebookComment | None = parent_comment
        self._parent_post: fb_post.FacebookPost | None = parent_post

        # initialize attributes that is not their data
        self._message: str | None = None
        self._reaction_count: int = 0
        self._page_reaction: (
            Literal["LIKE", "LOVE", "CARE", "HAHA", "WOW", "SAD", "ANGRY"] | None
        ) = None
        self._replies: dict[str, FacebookComment] = {}
        self._author: FacebookCommentAuthor | None = None
        self._attachment: FacebookCommentAttachment | None = None
        self._created_time: datetime = datetime.now()
        self._are_replies_available: bool = False
        self._next_replies_available: bool = False
        self._total_reply_count: int = 0
        self._next_available_reply_count: int = 0

        self._headers: dict[str, str] = {"Content-Type": "application/json"}
        self._initialized: bool = False
        self._current_reply_after_cursor: str | None = None

    # ===============================================
    #               USEFUL METHODS
    # ===============================================
    async def edit_comment(self, message: str, attachment: str | None = None) -> bool:
        """Edit the comment.

        Message is required since it will be removed when you only update
        the attachment without the message.

        Args:
            message: The new message written in the comment.
            attachment: If you wish to add images/videos to the comment.

        Raises:
            ValidationError: If something went wrong during validation of api response.
            ValueError: If you did not provide either message or attachment.
            RuntimeError: Something doesn't work with the code.

        """
        url = create_url_format(self.comment_id)
        data: dict[str, str] = {}
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

        # update message to the comment object
        self._message = message

        # update attachment to the comment object
        if attachment != None:
            # re-requesting to the api to get only the attachment data
            # this method is only what is available in order to get the attachment
            # data from the comment object. I tried the `me/photos` endpoint but
            # it is not enough, what if for the video attachment? video endpoints
            # are complicated and for the gif that uses animated_image_share, will
            # be almost impossible to get the attachment id from those endpoints.
            url = create_url_format(self.comment_id)
            params = {"access_token": self._access_token, "fields": "attachment"}
            response = await self._session.get(
                url=url, params=params, headers=self._headers
            )
            raise_for_status(response=response)

            if "attachment" not in response.json():
                raise RuntimeError("No attachment data from the comment object.")

            response_object = CommentAttachment.model_validate(
                response.json()["attachment"]  # finger cross we get this attachment
            )
            self._attachment = self._parse_attachment(response_object)

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

    async def add_reply_comment(
        self, message: str | None = None, attachment: str | None = None
    ) -> "FacebookComment":
        """Add a reply to the comment.

        The return object is a Comment object. You need to run
        `initialize_properties` method in order to access some data
        your need.

        Args:
            message: The new message written in the comment.
            attachment: If you wish to add images/videos to the comment.

        Raises:
            ValidationError: If something went wrong during validation of api response.
            ValueError: If you did not provide either message or attachment.

        Returns:
            a FacebookComment object.

        """
        comment_object = await self.ext_add_comment(
            id=self.comment_id,
            access_token=self._access_token,
            session=self._session,
            headers=self._headers,
            parent_comment=self,
            parent_post=self._parent_post,
            message=message,
            attachment=attachment,
        )

        # initialize properties
        # get the next cursor if available
        self._current_reply_after_cursor, _ = await asyncio.gather(
            self.ext_get_next_cursor(
                id=self.comment_id,
                access_token=self._access_token,
                session=self._session,
            ),
            comment_object.initialize_properties(),
        )

        # update reply count and reply objects
        self._total_reply_count += 1
        self._replies[comment_object.comment_id] = comment_object

        return comment_object

    async def get_more_reply_comments(
        self, limit: int | None = None
    ) -> list["FacebookComment"]:
        """Get the reply comments of the comment.

        Notes:
            Replies are automatically registered into the comment object.

        Tips:
            you can use `limit` parameter up to 100 to get all the
            comments in one scope, then another 100 later if there are more
            reply comments available.

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

        reply_comments: dict[str, FacebookComment] = {}

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
                parent_comment = self
                parent_id = ""
                if reply_comment.parent != None:
                    parent_id = reply_comment.parent.id

                if parent_id != self.comment_id:
                    if parent_id in reply_comments:
                        parent_comment = reply_comments[parent_id]
                    elif parent_id in self._replies:
                        parent_comment = self._replies[parent_id]

                    # This one is not needed since getting all reply comments
                    # handles all reply comments which means, all reply comments
                    # are available to be checked using self._replies
                    # and reply_comments
                    # else:
                    # creating a new comment because it might not
                    # exists on current replies due to cursor pagination
                    # and this one needs manual initialization
                    # parent_comment = FacebookComment(
                    #     comment_id=parent_id,
                    #     access_token=self._access_token,
                    #     session=self._session,
                    #     parent_comment=self,
                    #     parent_post=self._parent_post,
                    # )

                reply_comment_object = FacebookComment(
                    comment_id=reply_comment.id,
                    access_token=self._access_token,
                    session=self._session,
                    parent_comment=parent_comment,
                    parent_post=self.parent_post,
                )
                reply_comment_object.put_initialized_properties(
                    response_object=reply_comment
                )
                reply_comments[reply_comment_object.comment_id] = reply_comment_object

            # Note: not using the paging.next url because they don't retain
            #       the same parameters for fields
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
        self._replies.update(reply_comments)

        # update reply data
        self._next_available_reply_count = self._next_available_reply_count - len(
            reply_comments
        )
        self._next_replies_available = self._next_available_reply_count > 0

        # returning the current requested reply comments for
        # other uses
        return (
            list(reply_comments.values())[:limit]
            if limit
            else list(reply_comments.values())
        )

    async def refresh(self) -> None:
        """Refresh the comment object.

        Warning:
            Doing this will reset the comment object. Its reply
            objects will also be reset until to its maximum limited number.
            You need to run `get_reply_comments` again to get the all or some
            of the reply comments left.

        """
        # reset reply properties
        self._initialized = False
        self._replies = {}
        self._current_reply_after_cursor = None

        await self.initialize_properties()

    async def initialize_properties(self) -> None:
        """Fetch comment data from the Graph API and initialize properties."""
        if self._initialized:
            warnings.warn(
                f"Comment object: {self._comment_id} was already initialized. This method will have no effect"
            )
            return

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
    #           ATTRIBUTE PROPERTIES
    # ===============================================
    @property
    def comment_id(self) -> str:
        """The `id` of the comment."""
        return self._comment_id

    @property
    def parent_comment(self) -> "FacebookComment | None":
        """The parent comment of the comment."""
        return self._parent_comment

    @property
    def parent_post(self) -> "fb_post.FacebookPost | None":
        """The `id` of the author of the comment."""
        self._is_initialized()
        return self._parent_post

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
        return list(self._replies.values())

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
        """Whether the comment has replies."""
        self._is_initialized()
        return len(self._replies) > 0

    @property
    def next_replies_available(self) -> bool:
        """Whether the comment's replies can be retrieved using `get_reply_comments`.

        Notes:
            This is not for knowing if the comment has replies. Check if the `replies`
            property is not empty.

        """
        self._is_initialized()
        return self._next_replies_available

    @property
    def total_reply_count(self) -> int:
        """The total number of replies of the comment.

        Notes:
            The total number of replies from the facebook comment is not the
            same as the total number of replies from the current comment object.

            Use `total_available_reply_count` for the total number of replies
            available on the comment object.

        """
        self._is_initialized()
        return self._total_reply_count

    @property
    def total_available_reply_count(self) -> int:
        """The total number of replies available on the comment object."""
        self._is_initialized()
        return len(self._replies)

    @property
    def next_available_reply_count(self) -> int:
        """The number of available replies of the comment."""
        self._is_initialized()
        return self._next_available_reply_count

    @property
    def is_initialized(self) -> bool:
        """Whether the comment object is initialized."""
        return self._initialized

    # ===============================================
    #           CLASSMETHODS
    # ===============================================
    @classmethod
    async def ext_add_comment(
        cls,
        id: str,
        access_token: str,
        session: AsyncClient,
        headers: dict[str, str],
        parent_comment: "FacebookComment | None" = None,
        parent_post: "fb_post.FacebookPost | None" = None,
        message: str | None = None,
        attachment: str | None = None,
    ) -> "FacebookComment":
        """Add comment request object.

        Warning:
            Do not use this method directly from your code outside.
            This method is an internal helper for the official Facebook Post
            and Comment object.

        Args:
            id: The `id` of the post.
            access_token: The access token of the page.
            session: The httpx async session.
            headers: The headers of the request.
            parent_comment: The parent comment of the comment.
            parent_post: The parent post of the comment.
            message: The message written in the comment.
            attachment: If you wish to add images/videos to the comment.

        Raises:
            ValidationError: If something went wrong during validation of api response.
            ValueError: If you did not provide either message or attachment.

        Returns:
            a FacebookComment object.

        """
        url = create_url_format(f"{id}/comments")
        data: dict[str, str | None] = {}
        params = {"access_token": access_token}

        if message != None:
            data["message"] = message

        if attachment:
            if attachment.startswith("https://"):
                data["attachment_url"] = attachment
            elif exists(attachment):
                photo_id = await create_photo_id(
                    photo_url_or_path=attachment,
                    access_token=access_token,
                    session=session,
                )
                data["attachment_id"] = photo_id
            else:
                raise ValueError(
                    "Can't validate your attachment. Please ensure you provided a valid url or file path."
                )

        response = await session.post(
            url=url, params=params, headers=headers, json=data
        )
        raise_for_status(response)

        response_object: ObjectIdResponse = ObjectIdResponse.model_validate(
            response.json()
        )

        comment_object = FacebookComment(
            comment_id=response_object.id,
            access_token=access_token,
            session=session,
            parent_comment=parent_comment,
            parent_post=parent_post,
        )

        return comment_object

    @classmethod
    async def ext_get_next_cursor(
        cls, id: str, access_token: str, session: AsyncClient
    ) -> str | None:
        """Get the next cursor of the comment.

        Will return `None` if there are no `next` object
        instead of getting only the `after` object.

        Warning:
            Do not use this method directly from your code outside.
            This method is an internal helper for the official Facebook Post
            and Comment object.

        Args:
            id: The `id` of the post.
            access_token: The access token of the page.
            session: The httpx async session.

        """
        url = create_url_format(f"{id}/comments")
        params = {"access_token": access_token, "summary": "true", "limit": 0}
        response = await session.get(url, params=params)

        response_object = CommentData.model_validate(response.json())

        if response_object.paging and response_object.paging.next:
            return response_object.paging.cursors.after

        return None

    # ===============================================
    #           PRIVATE METHODS
    # ===============================================

    def _create_params(self) -> dict[str, str]:
        """Create the parameters for the Graph API request."""
        params = {
            "access_token": self._access_token,
            "fields": create_comment_fields(),
        }
        return params

    def _is_initialized(self) -> None:
        """Initialize the comment object."""
        if not self._initialized:
            raise Exception("Comment object is not initialized.")

    def _parse_attachment(
        self, attachment_object: CommentAttachment
    ) -> FacebookCommentAttachment:
        attachment_id = attachment_object.target.id

        match attachment_object.type:
            case "photo":
                media_type = "image"
            case "video_inline":
                media_type = "video"
            case "animated_image_share":
                media_type = "gif"

        if attachment_object.media.source != None:
            src = attachment_object.media.source
        else:
            src = attachment_object.media.image.src

        thumbnail_src = attachment_object.media.image.src

        facebook_url = attachment_object.target.url

        height = attachment_object.media.image.height
        width = attachment_object.media.image.width

        return FacebookCommentAttachment(
            attachment_id=attachment_id,
            src=src,
            thumbnail_src=thumbnail_src,
            facebook_url=facebook_url,
            height=height,
            width=width,
            media_type=media_type,
        )

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
            self._attachment = self._parse_attachment(response_object.attachment)

        # like count
        self._reaction_count = response_object.reactions.summary.total_count

        # page reaction
        self._page_reaction = response_object.reactions.summary.viewer_reaction

        # comment replies
        if response_object.comments != None:
            for comment in response_object.comments.data:
                parent_comment = self
                parent_id = ""
                if comment.parent != None:
                    parent_id = comment.parent.id

                if parent_id != self.comment_id:
                    if parent_id in self._replies:
                        parent_comment = self._replies[parent_id]
                    else:
                        # creating a new comment because it might not
                        # exists on current replies due to cursor pagination
                        # and this one needs manual initialization
                        parent_comment = FacebookComment(
                            comment_id=parent_id,
                            access_token=self._access_token,
                            session=self._session,
                            parent_comment=self,
                            parent_post=self._parent_post,
                        )

                reply_comment_object = FacebookComment(
                    comment_id=self.comment_id,
                    access_token=self._access_token,
                    session=self._session,
                    parent_comment=parent_comment,
                    parent_post=self._parent_post,
                )
                reply_comment_object.put_initialized_properties(response_object=comment)

                self._replies[reply_comment_object.comment_id] = reply_comment_object

            # overall reply count
            self._total_reply_count = response_object.comments.summary.total_count

            # available reply count
            self._next_available_reply_count = self._total_reply_count - len(
                self._replies
            )

            # are replies available
            self._next_replies_available = self._next_available_reply_count > 0

            if response_object.comments.paging and self._next_replies_available:
                self._current_reply_after_cursor = (
                    response_object.comments.paging.cursors.after
                )

        # set as initialized
        self._initialized = True

    # ===============================================
    #               OBJECT CONTROL
    # ===============================================
    __slots__: set[str] = {
        "_comment_id",
        "_message",
        "_access_token",
        "_session",
        "_parent_comment",
        "_parent_post",
        "_reaction_count",
        "_is_page_reacted",
        "_page_reaction",
        "_replies",
        "_author",
        "_attachment",
        "_created_time",
        "_are_replies_available",
        "_next_replies_available",
        "_total_reply_count",
        "_next_available_reply_count",
        "_headers",
        "_initialized",
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
            f"replies={len(self._replies)}, "
            f"next_replies_available={self._next_replies_available}, "
            f"total_reply_count={self._total_reply_count}, "
            f"available_reply_count={self._next_available_reply_count}, "
            f"author={self._author}, "
            f'attachment={"\"...\"" if self._attachment is not None else "None"}, '
            f"created_time={self._created_time}, "
            f"initialized={self.is_initialized}"
            f")"
        )

    @override
    def __eq__(self, other: object) -> bool:
        if isinstance(other, str):
            return (
                self.comment_id == other
                or self._message == other
                or (self._author.name == other if self._author is not None else False)
            )

        return False
