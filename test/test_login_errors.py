"""Testing login on official api."""

from fbtools.official.api import GraphSession
import asyncio
from fbtools.official.exceptions import LoginError
import pytest

official_api = GraphSession()


def test_raise_login_error():
    """Test if raise login error."""
    with pytest.raises(LoginError):
        asyncio.run(
            official_api.login_with_access_token(user_access_token="Wrongtoken")
        )
