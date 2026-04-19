"""User node of Facebook Graph API."""

from typing import Literal
from httpx import AsyncClient

from fbtools.models.users.response import LoginAsTokenResponse


class User:
    """User node of Facebook Graph API."""

    def __init__(
        self, user_id: str | Literal["me"] = "me", session: AsyncClient | None = None
    ):
        """Initialize user.

        Args:
            user_id: User ID or "me". The "me" is used on dev mode.
            session: Async Httpx Session.

        """
        # attributes
        self.user_id: str = user_id
        self.short_name: str | None = None

        # private attributes
        self._access_token: str | None = None

        # objects
        self._session: AsyncClient = (
            AsyncClient(base_url="https://graph.facebook.com/", timeout=60)
            if session is None
            else session
        )

    # Public Methods
    async def login_with_access_token(
        self, user_access_token: str, skip_validation: bool = False
    ) -> None:
        """Login with access token.

        Args:
            user_access_token: User access token.
            skip_validation: Skip validation of access token.

        Raises:
            ClientResponseError: Response error.

        """
        if not skip_validation:
            params = {"access_token": user_access_token, "fields": "short_name"}
            response = await self._session.get(self.user_id, params=params)
            response = response.raise_for_status()
            response_data = LoginAsTokenResponse.model_validate(await response.json())
            self.user_id = response_data.id
            self.short_name = response_data.short_name

        self._access_token = user_access_token

    async def generate_access_token(self) -> None:
        """Generate user access token."""
        raise NotImplementedError("This feature is not implemented yet.")
