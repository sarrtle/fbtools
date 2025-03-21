"""All common utility functions for official APIs."""

from datetime import datetime, timedelta, timezone
from collections.abc import AsyncGenerator
from aiofiles import open as aopen

from httpx import HTTPStatusError, Response

from fbtools.official.utilities.global_instances import GraphApiVersion

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
