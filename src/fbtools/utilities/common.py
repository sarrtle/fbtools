"""Common utilties."""

from urllib.parse import urlparse

from httpx import HTTPStatusError, Response

from fbtools.utilities.global_instance import GraphApiVersion


def create_base_url() -> str:
    """Create a url format for the Facebook Graph API."""
    current_version = GraphApiVersion.get_version()
    return f"https://graph.facebook.com/{current_version}"


def is_url_valid(url: str) -> bool:
    """Check if url is valid."""
    result = urlparse(url)
    return all([result.scheme in ("http", "https"), result.netloc])


def raise_for_status(response: Response):
    """Raise for status."""
    if response.status_code != 200:
        raise HTTPStatusError(
            message=f"{response.status_code} {response.text}",
            request=response.request,
            response=response,
        )
