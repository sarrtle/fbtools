"""Base api object for all official APIs."""

from httpx import AsyncClient

from fbtools.official.exceptions import LoginError, UserValidationError


class GraphSession:
    """Base api object for all official APIs.

    Attributes:
        access_token: The user access token created from facebook developer tools.

    """

    def __init__(self):
        """Initialize FbtoolsOfficial."""
        # attributes
        self.access_token: str | None = None

        # objects
        self.session: AsyncClient = AsyncClient(base_url="https://graph.facebook.com/")

    # login methods
    async def login_with_access_token(
        self, user_access_token: str, skip_validation: bool = False
    ):
        """Directly using your generated access token.

        Args:
            user_access_token: The user access token created from facebook developer tools.
            skip_validation: Skip validation of the access token.

        Raises:
            LoginError: If something went wrong during login.

        """
        # need validation of the token before use
        if not skip_validation:
            # short name is for the user only, page validation will be on
            # another method.
            params = {"access_token": user_access_token, "fields": "short_name"}
            response = await self.session.get("me", params=params)

            if response.status_code != 200:
                raise LoginError(error_type=UserValidationError(response.text))

        self.access_token = user_access_token

    # local utilities
    def _create_httpx_session(self) -> AsyncClient:
        """Create an asynchronous httpx session."""
        return AsyncClient(base_url="https://graph.facebook.com/")
