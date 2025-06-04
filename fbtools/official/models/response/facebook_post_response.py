"""Response objects for Facebook Graph API."""

from datetime import datetime
import json
from typing import Literal
from pydantic import BaseModel, ValidationError, model_validator

from fbtools.official.models.response.facebook_comment_response import CommentData


class BatchResponseBase(BaseModel):
    """Base object for batch response that requires validation."""

    @model_validator(mode="before")
    def _parse_body_to_dict(cls, values: dict[str, dict[str, str] | str | object]):
        raw_body = values.get("body")

        if raw_body is None:
            raise ValidationError("body was not found in batch response.")

        parsed: dict[str, str]

        if isinstance(raw_body, str):
            try:
                parsed = json.loads(raw_body)
            except json.JSONDecodeError as exc:
                raise ValidationError from exc
        elif isinstance(raw_body, dict):
            parsed = raw_body
        else:
            raise ValidationError("body was not a string or a dict in batch response.")

        values["body"] = parsed
        return values


class BatchResponseForPost(BatchResponseBase):
    """Batch post response from Facebook Graph API."""

    code: int
    body: "FacebookPostResponse"


class BatchResponseForCommentCount(BatchResponseBase):
    """Batch comment count response from Facebook Graph API."""

    code: int
    body: "AllCommentCount"


class AllCommentCount(BaseModel):
    """Counting all comments using stream."""

    data: list[str] = []
    summary: "SummaryForCount"


class SummaryForCount(BaseModel):
    """Summary for comment count."""

    order: Literal["chronological"]
    total_count: int
    can_comment: bool


class FacebookPostResponse(BaseModel):
    """Post response from Facebook Graph API.

    Notes:
        if attachment is a multiple video, status_type
        will still be "added_photos". I don't know why.

    """

    id: str
    message: str | None = None
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
    ) = None
    story: str | None = None
    created_time: datetime
    attachments: "FacebookPostAttachment | None" = None
    comments: "CommentData | None" = None
    reactions: "Reaction | None" = None
    shares: "ShareData | None" = None


class FacebookPostAttachment(BaseModel):
    """Attachment data from Facebook Graph API."""

    data: list["FacebookPostAttachmentData"]


class FacebookPostAttachmentData(BaseModel):
    """Attachment data from Facebook Graph API.

    Notes:
        If media is None, then it is a video.

    """

    media: "MediaData | None" = None
    type: Literal["album", "photo", "video_inline", "profile_media", "native_templates"]
    description: str | None = None
    title: str | None = None
    subattachments: "Subattachments | None" = None
    unshimmed_url: str
    target: "TargetData"


class Subattachments(BaseModel):
    """Subattachments data from Facebook Graph API.

    If there will be many attachments, it will be in a list.
    """

    data: list["SubattachmentsData"]


class SubattachmentsData(BaseModel):
    """Subattachments data from Facebook Graph API."""

    description: str | None = None
    media: "MediaData"
    target: "TargetData"
    type: Literal["photo", "video"]
    url: str


class TargetData(BaseModel):
    """Target data from Facebook Graph API.

    Where the attachment ID (image/video) is set
    and the url of the attachment.
    """

    id: str
    url: str


class MediaData(BaseModel):
    """Media data from Facebook Graph API.

    If attachment is a multiple video, the key is still
    `image`. I don't know why.
    """

    image: "MediaProperties"
    source: str | None = None


class MediaProperties(BaseModel):
    """Image data from Facebook Graph API."""

    height: int
    src: str
    width: int


class Reaction(BaseModel):
    """Reaction field."""

    data: list["ReactionData"]
    paging: "PagingData | None" = None
    summary: "SummaryData"


# TODO: This is seem redundant, put them on common field
#       models
class PagingData(BaseModel):
    """Paging data."""

    cursors: "CursorData"
    next: str | None = None


class CursorData(BaseModel):
    """Cursor data."""

    before: str
    after: str


class SummaryData(BaseModel):
    """Summary data."""

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


class ReactionData(BaseModel):
    """Reaction data."""

    id: str
    name: str
    type: Literal["LIKE", "LOVE", "CARE", "HAHA", "WOW", "SAD", "ANGRY"]


class ShareData(BaseModel):
    """Share data."""

    count: int


FacebookPostResponse.model_rebuild()
