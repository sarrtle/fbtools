"""Response objects for Facebook Graph API."""

from datetime import datetime
from typing import Literal
from pydantic import BaseModel


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


FacebookPostResponse.model_rebuild()
