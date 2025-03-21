"""Facebook comment respone object."""

from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field, ValidationError, model_validator

# pyright: reportAny=false


class FacebookCommentResponse(BaseModel):
    """FacebookCommentResponse object."""

    created_time: datetime
    from_: "CommentFrom | None" = Field(default=None, alias="from")
    id: str
    reactions: "CommentReaction"
    message: str | None = None
    attachment: "CommentAttachment | None" = None
    user_likes: bool
    permalink_url: str
    comments: "CommentData | None" = None


class CommentFrom(BaseModel):
    """CommentFrom object."""

    name: str
    id: str


class CommentReaction(BaseModel):
    """CommentReaction object."""

    data: list["CommentReactionData"]
    paging: "CommentPaging | None" = None
    summary: "CommentReactionSummary"


class CommentPaging(BaseModel):
    """CommentReactionPaging object."""

    cursors: "CursorItem"
    next: str | None = None


class CursorItem(BaseModel):
    """CursorItem object."""

    before: str
    after: str


class CommentReactionSummary(BaseModel):
    """CommentReactionSummary object."""

    total_count: int
    viewer_reaction: (
        Literal["LIKE", "LOVE", "CARE", "HAHA", "WOW", "SAD", "ANGRY"] | None
    ) = None

    @model_validator(mode="before")
    def _validate_page_reaction(cls, values: dict[str, str | None]):
        if "viewer_reaction" not in values:
            raise ValidationError(
                "`viewer_reaction` was not found in reaction summary."
            )

        if values["viewer_reaction"] == "NONE":
            values["viewer_reaction"] = None
        return values


class CommentReactionData(BaseModel):
    """CommentReactionData object."""

    id: str
    name: str
    profile_type: Literal["user"]  # will add more in the future
    pic_large: str
    pic_small: str
    can_post: bool
    type: Literal["LIKE", "LOVE", "CARE", "HAHA", "WOW", "SAD", "ANGRY"]


class CommentData(BaseModel):
    """CommentData object."""

    data: list[FacebookCommentResponse]
    paging: CommentPaging | None = None
    summary: "CommentDataSummary"


class CommentDataSummary(BaseModel):
    """CommentDataSummary object."""

    order: Literal["chronological"]
    total_count: int
    can_comment: bool


class CommentAttachment(BaseModel):
    """CommentAttachment object."""

    media: "MediaData"
    target: "TargetData"
    type: Literal["photo", "video_inline", "animated_image_share"]
    url: str


class MediaData(BaseModel):
    """MediaData object."""

    image: "ImageData"
    source: str | None = None


class ImageData(BaseModel):
    """ImageData object."""

    height: int
    src: str
    width: int


class TargetData(BaseModel):
    """TargetData object."""

    id: str | None = None
    url: str
