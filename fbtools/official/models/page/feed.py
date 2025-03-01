"""Feed field webhook.

Notes:
    Available to import:
        1. Feed
        2. FeedNewPost
        3. FeedNewPostWithPhoto
        4. FeedNewPostWithManyPhotos
        5. FeedNewPostWithVideo
        6. FeedComment
        7. FeedCommentWithPhoto
        8. FeedCommentWithVideo

Notes:
    on feed comment:
        - if comment has no text, the message will be None
        - the video and gif have the same variable `video` so gif
            and video must be on FeedCommentWithVideo, FeedCommentReplyWithVideo
        - There are some case that the video variable will not found even you
            commented with video or gif. It will automatically go to FeedComment.

Notes:
    on video posts:
        - reels and video posts are the same.
        - description in reels are the same as `message` in videos as caption content.
        - when you edit the video in video editing section of facebook before uploading,
            you see title, another title plus more and tags.
            - the title and the last title you made will be use in `message` variable as
                post caption.
            - tags are not included in feed webhook for video posts.
        - posting many videos at once will make the webhook send them one by one but on the
            same post id. Who would track the post id to combine them.

Notes:
    watch out on `edited` verb, it indicates that the post or comment was edited.

Developer's Note:
    - I chose forward reference to follow the structure of the original
        json responses from the webhook.
    - Having the objects needed to edit and import at the top of the file is easier
        than finding them anywhere in this file.

"""

from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field, model_validator


class Feed(BaseModel):
    """Feed field data.

    Attributes:
        id: The id of the webhook.
        time: The time webhook received.
        changes: What kind of event happened.

    """

    id: str
    time: int
    changes: list["FeedValueType"]


class FeedValueType(BaseModel):
    """Type of the feed.

    Attributes:
        field: The type of changes happened.
        value: The data of the feed. Either status feed or comment feed.

    """

    field: Literal["feed"]
    value: """(
        FeedNewPost
        | FeedNewPostWithPhoto
        | FeedNewPostWithManyPhotos
        | FeedComment
        | FeedCommentWithPhoto
        | FeedCommentWithVideo
    )"""


class FeedNewPost(BaseModel):
    """Status feed that is a single text post."""

    from_: "FeedFrom" = Field(..., alias="from")
    message: str
    post_id: str
    created_time: int
    item: Literal["status"]
    published: int
    verb: Literal["add", "edited"]


class FeedNewPostWithPhoto(BaseModel):
    """Status feed that has a single attachment.

    Attributes:
        from: Who created the post.
        link: The url of the image
        message: The text content of the post.
        post_id: The id of the post.
        created_time: The time of the post creation.
        item: What type of feed is it.
        photo_id: The id of the image.
        published: The time of the post creation.
        verb: The action of the feed.

    """

    from_: "FeedFrom" = Field(..., alias="from")
    link: str
    message: str
    post_id: str
    created_time: int
    item: Literal["photo"]
    photo_id: str
    published: int
    verb: Literal["add", "edited"]


class FeedNewPostWithManyPhotos(BaseModel):
    """Status feed that has multiple attachments.

    When the page create a new post with multiple images.

    Attributes:
        from: Who created the post.
        link: The url of the image
        message: The text content of the post.
        photos: The list of urls of the images.
        post_id: The id of the post.
        created_time: The time of the post creation.
        item: What type of feed is it.
        published: The time of the post creation.
        verb: The action of the feed.

    """

    from_: "FeedFrom" = Field(..., alias="from")
    link: str
    message: str
    photos: list[str]
    post_id: str
    created_time: int
    item: Literal["status"]
    published: int
    verb: Literal["add", "edited"]


class FeedNewPostWithVideo(BaseModel):
    """Video feed data.

    Attributes:
        from: Who created the post.
        link: The url of the video.
        message: The text content of the post.
        post_id: The id of the post.
        created_time: The time of the post creation.
        item: What type of feed is it.
        published: The time of the post creation.
        verb: The action of the feed.

    """

    from_: "FeedFrom" = Field(..., alias="from")
    link: str
    message: str | None
    post_id: str
    created_time: int
    item: Literal["video"]
    published: int
    verb: Literal["add", "edited"]
    video_id: str


class FeedComment(BaseModel):
    """Comment Feed data.

    When the page, or other users commented on your post.

    Attributes:
        from: The sender of the comment.
        post: The data of the post where the comment was made.
        message: The message of the comment.
        post_id: The id of the post.
        comment_id: The id of the comment.
        created_time: The time of the comment creation in timestamp format.
        item: What type of feed is it. Either comment, status or a photo.
        parent_id: The id of the post or the parent comment.
        verb: The action of the feed.
        is_reply: Whether the comment is a reply or not.

    """

    from_: "FeedFrom" = Field(..., alias="from")
    post: "FeedPostData"
    message: str
    post_id: str
    comment_id: str
    created_time: int
    item: Literal["comment"]
    parent_id: str
    verb: Literal["add", "edited"]

    is_reply: bool = False

    @model_validator(mode="after")
    def _check_if_top_level_comment(self):
        # for reply comment, parent_id is not the same as post_id
        self.is_reply = self.parent_id != self.post_id
        return self


class FeedCommentWithPhoto(BaseModel):
    """Comment Feed data.

    When the page, or other users commented on your post.

    Attributes:
        from: The sender of the comment.
        post: The data of the post where the comment was made.
        message: The message of the comment.
        photo: The url of the image of the comment
        post_id: The id of the post.
        comment_id: The id of the comment.
        created_time: The time of the comment creation in timestamp format.
        item: What type of feed is it. Either comment, status or a photo.
        parent_id: The id of the post or the parent comment.
        verb: The action of the feed.
        is_reply: Whether the comment is a reply or not.

    """

    from_: "FeedFrom" = Field(..., alias="from")
    post: "FeedPostData"
    message: str | None
    photo: str
    post_id: str
    comment_id: str
    created_time: int
    item: Literal["comment"]
    parent_id: str
    verb: Literal["add", "edited"]

    is_reply: bool = False

    @model_validator(mode="after")
    def _check_if_top_level_comment(self):
        # for reply comment, parent_id is not the same as post_id
        self.is_reply = self.parent_id != self.post_id
        return self


class FeedCommentWithVideo(BaseModel):
    """Comment Feed data with video or gif.

    When the page, or other users commented on your post.

    Attributes:
        from: The sender of the comment.
        post: The data of the post where the comment was made.
        message: The message of the comment.
        video: The url of the video of the comment
        post_id: The id of the post.
        comment_id: The id of the comment.
        created_time: The time of the comment creation in timestamp format.
        item: What type of feed is it. Either comment, status or a photo.
        parent_id: The id of the post or the parent comment.
        verb: The action of the feed.
        is_reply: Whether the comment is a reply or not.

    """

    from_: "FeedFrom" = Field(..., alias="from")
    post: "FeedPostData"
    message: str | None
    video: str
    post_id: str
    comment_id: str
    created_time: int
    item: Literal["comment"]
    parent_id: str
    verb: Literal["add", "edited"]

    is_reply: bool = False

    @model_validator(mode="after")
    def _check_if_reply_comment(self):
        # for reply comment, parent_id is not the same as post_id
        self.is_reply = self.parent_id != self.post_id
        return self


class FeedFrom(BaseModel):
    """From data.

    Attributes:
        name: The name of commenter.
        id: The psid.

    """

    name: str
    id: str


class FeedPostData(BaseModel):
    """Post data.

    Attributes:
        id: The id of the post.

    """

    status_type: Literal["mobile_status_update"]
    is_published: bool
    updated_time: datetime
    permalink_url: str
    promotion_status: Literal["inactive"]
    id: str


Feed.model_rebuild()
