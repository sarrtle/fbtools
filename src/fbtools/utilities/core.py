"""Core utilities for the APIs."""

from pathlib import Path
from typing import Literal
from aiofiles import open as aopen
from httpx import AsyncClient

from fbtools.models.page.id_response import IdResponse
from fbtools.utilities.common import is_url_valid


async def create_photo_id(
    photo_url_or_file_path: str,
    access_token: str,
    session: AsyncClient,
    user_id: str | Literal["me"] = "me",
) -> str:
    """Create photo id from url or local image file.

    Args:
        photo_url_or_file_path: The url or local image file path.
        access_token: Page access token.
        session: Async Httpx Session.
        user_id: User ID or "me". The "me" is used on dev mode.

    Returns:
        The photo id.

    Raises:
        ValueError: If the photo url or file path is invalid.

    """
    data: dict[str, str | bool] = {}
    file: dict[str, bytes] | None = None

    # so the photo won't be uploaded on your feed
    # we only need the photo id
    data["published"] = False

    # proper way to check if the url is valid
    if is_url_valid(photo_url_or_file_path):
        data["url"] = photo_url_or_file_path

    # check if the file path is valid and exists
    elif Path(photo_url_or_file_path).is_file():
        async with aopen(photo_url_or_file_path, mode="rb") as f:
            file = {"source": await f.read()}
    else:
        raise ValueError(f"Invalid photo url or file path: {photo_url_or_file_path}")

    params = {"access_token": access_token}

    response = await session.post(
        f"{user_id}/photos", data=data, params=params, files=file
    )

    response_id = IdResponse.model_validate(response.json())
    return response_id.id
