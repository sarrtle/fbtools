"""Feed field webhook.

Notes:
    on feed comment:
        - if comment has no text, the message will be None
        - the video and gif have the same variable `video` so gif
            and video must be on FeedCommentWithVideo
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

# reusable types
REACTION_TYPES = Literal["like", "love", "wow", "care", "haha", "sad", "angry"]
REACTION_VERB_TYPES = Literal["add", "remove", "edit"]
FEED_VERB_TYPES = Literal["add", "edited", "remove"]


class FacebookFeed(BaseModel):
    """Type of the feed.

    Attributes:
        field: The type of changes happened.
        value: The data of the feed. Either status feed or comment feed.

    """

    field: Literal["feed"]
    value: """(
        FeedNewReactionOnPost
        | FeedNewReactionOnComment
        | FeedNewPost
        | FeedNewPostWithPhoto
        | FeedNewPostWithManyPhotos
        | FeedNewPostWithVideo
        | FeedComment
        | FeedCommentWithPhoto
        | FeedCommentWithVideo
    )"""


class FeedNewReactionOnPost(BaseModel):
    """When someone react on your post."""

    from_: "FeedFrom" = Field(..., alias="from")
    post_id: str
    created_time: int
    item: Literal["reaction"]
    parent_id: str
    reaction_type: REACTION_TYPES
    verb: REACTION_VERB_TYPES


class FeedNewReactionOnComment(BaseModel):
    """When someone react on your post."""

    from_: "FeedFrom" = Field(..., alias="from")
    post_id: str
    comment_id: str
    created_time: int
    item: Literal["reaction"]
    parent_id: str
    reaction_type: REACTION_TYPES
    verb: REACTION_VERB_TYPES


class FeedNewPost(BaseModel):
    """Status feed that is a single text post."""

    from_: "FeedFrom" = Field(..., alias="from")
    message: str
    post_id: str
    created_time: int
    item: Literal["status"]
    published: int
    verb: FEED_VERB_TYPES


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
    message: str | None = None
    post_id: str
    created_time: int
    item: Literal["photo"]
    photo_id: str
    published: int
    verb: FEED_VERB_TYPES


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
    message: str | None = None
    photos: list[str]
    post_id: str
    created_time: int
    item: Literal["status"]
    published: int
    verb: FEED_VERB_TYPES


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
    verb: FEED_VERB_TYPES
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
    verb: FEED_VERB_TYPES

    is_reply: bool = False

    @model_validator(mode="after")
    def _check_if_top_level_comment(self):
        # for reply comment, parent_id will hold the id of the parent comment
        # parent comment will use the second id of the post id after underscore `"_"`
        # to the first id of its own and the second id is the comment id after
        # underscore '"_"`

        unique_post_id = self.post_id.split("_")[1]
        is_parent_id_comment = self.parent_id.split("_")[0] == unique_post_id

        self.is_reply = is_parent_id_comment
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
    verb: FEED_VERB_TYPES

    is_reply: bool = False

    @model_validator(mode="after")
    def _check_if_top_level_comment(self):
        # for reply comment, parent_id will hold the id of the parent comment
        # parent comment will use the second id of the post id after underscore `"_"`
        # to the first id of its own and the second id is the comment id after
        # underscore '"_"`

        unique_post_id = self.post_id.split("_")[1]
        is_parent_id_comment = self.parent_id.split("_")[0] == unique_post_id

        self.is_reply = is_parent_id_comment
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
    verb: FEED_VERB_TYPES

    is_reply: bool = False

    @model_validator(mode="after")
    def _check_if_top_level_comment(self):
        # for reply comment, parent_id will hold the id of the parent comment
        # parent comment will use the second id of the post id after underscore `"_"`
        # to the first id of its own and the second id is the comment id after
        # underscore '"_"`

        unique_post_id = self.post_id.split("_")[1]
        is_parent_id_comment = self.parent_id.split("_")[0] == unique_post_id

        self.is_reply = is_parent_id_comment
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

    status_type: Literal["mobile_status_update", "added_photos", "added_video"]
    is_published: bool
    updated_time: datetime
    permalink_url: str
    promotion_status: Literal["inactive", "ineligible"]
    id: str


FacebookFeed.model_rebuild()
