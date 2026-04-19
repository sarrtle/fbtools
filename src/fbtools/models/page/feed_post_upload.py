"""Upload data model for feed post.

Exposed models:
    1. FeedPostUploadData
    2. AttachedMedia
"""

from typing import Annotated
from pydantic import BaseModel, Field, field_serializer


def exclude_none(v: list["AttachedMedia"] | None):
    """Exclude None values."""
    return v == []


def exclude_false(v: bool):
    """Exclude False values."""
    return v is False


class FeedPostUploadData(BaseModel):
    """Upload data model for feed post."""

    message: str | None
    published: Annotated[bool, Field(exclude_if=exclude_false)] = True
    attached_media: Annotated[
        list["AttachedMedia"] | None, Field(exclude_if=exclude_none)
    ] = []

    @field_serializer("message")
    def edit_message(self, value: str | None):
        """Empty string if value is None."""
        return "" if value is None else value

    @field_serializer("attached_media")
    def edit_attached_media(self, value: list["AttachedMedia"] | None):
        """Empty list if value is None."""
        return [] if value is None else value


class AttachedMedia(BaseModel):
    """Attached media model."""

    media_fbid: str
