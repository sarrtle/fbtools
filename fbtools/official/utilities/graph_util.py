"""Common graph api utilities.

This module fixes some of the cycle import why they have
to be separated and reused in an object.
"""

from os.path import exists
from typing import Literal
from aiofiles.threadpool.binary import AsyncBufferedReader
from httpx import AsyncClient
from aiofiles import open as aopen


async def create_photo_id(
    photo_url_or_path: str,
    access_token: str,
    session: AsyncClient,
    user_id: str | Literal["me"] = "me",
) -> str:
    """Upload photo to Facebook and get their photo id.

    Args:
        photo_url_or_path: The photo url or local path.
        access_token: The access token of the page.
        session: The httpx async session.
        attachmend_id_only: Whether to return the attachment id only without publishing.
        user_id: The user id or "me". The "me" is used on dev/solo mode.

    Raises:
        FileNotFoundError: If file does not exist.
        Exception: If something went wrong when `id` was not found.

    """
    data: dict[str, str | bool | AsyncBufferedReader] = {"published": False}

    if photo_url_or_path.startswith("http"):
        data["url"] = photo_url_or_path
    else:
        if exists(photo_url_or_path):
            async with aopen(photo_url_or_path, "rb") as f:
                data["source"] = f
        else:
            raise FileNotFoundError(f"File {photo_url_or_path} does not exist.")

    params = {"access_token": access_token}
    response = await session.post(f"{user_id}/photos", data=data, params=params)

    response_data: dict[str, str] = response.json()

    if "id" not in response_data:
        # TODO: Make an exception for this
        raise Exception(response.text)

    return response_data["id"]
