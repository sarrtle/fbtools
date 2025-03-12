"""Attachment object."""

from typing import Literal


class Attachment:
    """Attachment object."""

    def __init__(
        self,
        attachment_id: str,
        src: str,
        thumbnail_src: str,
        facebook_url: str,
        description: str | None,
        height: int,
        width: int,
        media_type: Literal["image", "video", "image_profile", "video_reel"],
    ):
        """Initialize the Attachment object.

        Args:
            attachment_id: The ID of the attachment (image/video).
            src: The source url of the attachment.
            thumbnail_src: The thumbnail of the video for the attachment.
            facebook_url: The URL to facebook post that views the attachment.
            description: The description of the attachment.
            height: The height of the attachment.
            width: The width of the attachment.
            media_type: The type of the attachment.

        """
        self.attachment_id: str = attachment_id
        self.src: str = src
        self.thumbnail_src: str = thumbnail_src
        self.facebook_url: str = facebook_url
        self.description: str | None = description
        self.height: int = height
        self.width: int = width
        self.media_type: Literal["image", "video", "image_profile", "video_reel"] = (
            media_type
        )
