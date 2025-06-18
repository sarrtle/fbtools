"""Facebook message attachment."""

from typing import Literal, TypedDict


class FbMessageAttachment_Dict(TypedDict):
    """Facebook message attachment dictionary."""

    source: str
    attachment_type: Literal["image", "video", "audio", "file"]
