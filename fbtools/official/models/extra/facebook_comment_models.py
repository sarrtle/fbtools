"""Facebook comment attachment object."""

from typing import Literal, override


class FacebookCommentAttachment:
    """FacebookCommentAttachment object."""

    def __init__(
        self,
        attachment_id: str | None,
        src: str,
        thumbnail_src: str,
        facebook_url: str,
        height: int,
        width: int,
        media_type: Literal["image", "video", "gif"],
    ) -> None:
        """Initialize FacebookCommentAttachment.

        Attachment id is optional because media_type: gif doesn't
        have attachment id.

        Args:
            attachment_id: The ID of the attachment (image/video).
            src: The source url of the attachment.
            thumbnail_src: The thumbnail of the video for the attachment.
            facebook_url: The URL to facebook post that views the attachment.
            height: The height of the attachment.
            width: The width of the attachment.
            media_type: The type of the attachment.

        """
        self.attachment_id: str | None = attachment_id
        self.src: str = src
        self.thumbnail_src: str = thumbnail_src
        self.facebook_url: str = facebook_url
        self.height: int = height
        self.width: int = width
        self.media_type: Literal["image", "video", "gif"] = media_type

    @override
    def __repr__(self) -> str:
        return (
            f"FacebookCommentAttachment("
            f"attachment_id={self.attachment_id}, "
            f"src={self.src}, "
            f"thumbnail_src={self.thumbnail_src}, "
            f"facebook_url={self.facebook_url}, "
            f"height={self.height}, "
            f"width={self.width}, "
            f"media_type={self.media_type}"
            f")"
        )


class FacebookCommentAuthor:
    """FacebookCommentAuthor: Firstname Lastname."""

    def __init__(self, id: str, name: str) -> None:
        """Initialize FacebookCommentAuthor.

        Args:
            id: The ID of the author.
            name: The name of the author.

        """
        self.id: str = id
        self.name: str = name

    @override
    def __repr__(self) -> str:
        return f"FacebookCommentAuthor(id={self.id}, name={self.name})"
