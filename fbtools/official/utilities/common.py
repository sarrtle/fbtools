"""All common utility functions for official APIs."""

from datetime import datetime, timedelta, timezone


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
