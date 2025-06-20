"""All common utility functions for official APIs."""

import mimetypes
from typing import Hashable, cast
from datetime import datetime, timedelta, timezone
from collections.abc import AsyncGenerator
from os.path import exists
from urllib.parse import urlparse
from aiofiles import open as aopen

from cachetools import cached
from httpx import AsyncClient, HTTPStatusError, Response

from fbtools.official.utilities.global_instances import Cache, GraphApiVersion

CHUNK_SIZE = 4 * 1024 * 1024


def get_expiration_date(expires_in: int) -> str:
    """Convert expires_in seconds to a readable date.

    Args:
        expires_in: The number of seconds until expiration.

    Returns:
        The expiration date in the format "YYYY-MM-DD HH:MM:SS UTC".

    """
    expiration_time = datetime.now(tz=timezone.utc) + timedelta(seconds=expires_in)
    return expiration_time.strftime("%Y-%m-%d %H:%M:%S UTC")


def create_url_format(path: str):
    """Create a url format for the Facebook Graph API."""
    current_version = GraphApiVersion.get_version()
    return f"https://graph.facebook.com/{current_version}/{path}"


async def read_file_in_chunks(
    filepath: str, start_offset: int = 0, chunk_size: int = CHUNK_SIZE
) -> AsyncGenerator[bytes]:
    """Async generator that reads a file in chunks starting from given offset."""
    async with aopen(filepath, "rb") as file:
        await file.seek(start_offset)
        while chunk := await file.read(chunk_size):
            yield chunk


def raise_for_status(response: Response):
    """Raise exceptions for httpx response.

    Args:
        response: The httpx response.

    Raises:
        HttpStatusError: If http status code is not 200.

    """
    # raise common exception status
    if response.status_code != 200:
        raise HTTPStatusError(
            message=f"{response.status_code} {response.text}",
            request=response.request,
            response=response,
        )


def create_comment_fields() -> str:
    """Create the comment parameters for the Graph API request."""
    comment_fields = [
        "created_time",
        "parent",
        "from",
        "id",
        "attachment",
        "like_count",
        "message",
        "user_likes",
        "reactions.summary(true)",
        "permalink_url",
        "object",
        "comments.summary(true)",
        "likes",
    ]

    reaction_fields = [
        "id",
        "name",
        "type",
        "username",
        "profile_type",
        "pic_large",
        "pic_small",
        "link",
        "can_post",
    ]

    # add reaction fields on the comment
    comment_fields[
        comment_fields.index("reactions.summary(true)")
    ] += "{%s}" % ",".join(reaction_fields)

    # add comment fields on the comment
    comment_fields[comment_fields.index("comments.summary(true)")] += "{%s}" % ",".join(
        comment_fields
    )

    return ",".join(comment_fields)


def _attachment_key(attachment: str, **_kwargs: Hashable) -> str:
    return attachment


@cached(cache=Cache.get_cache(), key=_attachment_key)
async def get_attachment_mimetype(
    attachment: str, session: AsyncClient
) -> tuple[str, str]:
    """Get the mimetype of the attachment.

    It supports all kind of attachment like attachment url, local file or an
    attachment id,
    """
    print("Running get_attachment_mimetype")
    # custom header for anti robots
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:139.0) Gecko/20100101 Firefox/139.0"
    }
    # to return
    mimetype_value: tuple[str, str] = ("", "")

    if attachment.startswith("https://"):
        response = await session.head(url=attachment, headers=headers)
        try:
            raise_for_status(response)
            # - using cast to silent linters because we know that we are
            #   getting a string
            content_type = cast(str, response.headers.get("Content-Type", ""))
            mimetype_value = (content_type.split("/")[0], content_type)
        except HTTPStatusError as hse:
            # fallback to detecting extension from url
            parse_url = urlparse(attachment)
            filepath = parse_url.path

            mimetype, _ = mimetypes.guess_type(filepath)

            if mimetype is None:
                raise Exception(f"Could not determine mimetype from url\n{hse}")

            mimetype_value = (mimetype.split("/")[0], mimetype)
    elif exists(attachment):
        mimetype, _ = mimetypes.guess_type(attachment)

        if mimetype is None:
            raise Exception("Could not determine mimetype from attachment file.")

        mimetype_value = (mimetype.split("/")[0], mimetype)
    elif attachment.isdigit():
        raise Exception(
            "Attachment id is not supported. Use dictionary format instead and you must provide your own mimetype."
        )
    else:
        raise Exception("Invalid attachment source.")

    return mimetype_value
