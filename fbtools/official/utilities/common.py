"""All common utility functions for official APIs."""

from datetime import datetime, timedelta, timezone

from httpx import AsyncClient

from fbtools.official.models.page.post import FacebookPost
from fbtools.official.models.response.graph import FacebookPostResponse
from fbtools.official.utilities.global_instances import GraphApiVersion


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


async def create_post_object(post_id: str, access_token: str, session: AsyncClient):
    """Get post data and return as an object.

    Args:
        post_id: The id of the post.
        access_token: The access token of the page.
        session: The httpx async session.

    Returns:
        The FacebookPost object.

    Raises:
        ValidationError: If something went wrong during validation of api response.

    """
    url = create_url_format(post_id)
    params = {"access_token": access_token}
    response = await session.get(url, params=params)

    response_object = FacebookPostResponse.model_validate(response.json())

    return FacebookPost(
        post_id=response_object.id,
        message=response_object.message,
        status_type=response_object.status_type,
        story=response_object.story,
        created_time=response_object.created_time,
    )
