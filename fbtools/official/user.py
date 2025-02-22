"""User object Facebook of node."""

from httpx import AsyncClient

from fbtools.official.exceptions import (
    GenerateUserAccessTokenError,
    LoginError,
    UserValidationError,
)
from fbtools.utilities.fbauthflow import FacebookAuthFlow


class User:
    """User Node of Facebook.

    All user related APIs will be here.

    Attributes:
        access_token: The user access token created from facebook developer tools.
        session: An asynchronous httpx session.

    """

    def __init__(self):
        """Initialize User."""
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

    async def generate_access_token(self, client_id: str, client_secret: str):
        """Will automatically generate user access token using Facebook Login.

        Opens a browser and connect to your app, then generate the access token.

        Warning:
            1. This method will block the main thread.
            2. Must use locally only not on deployment server.

        Args:
            client_id: The client ID for the Facebook app.
            client_secret: The client secret for the Facebook app.

        Raises:
            LoginError: If can't generate user access token.

        """
        auth = FacebookAuthFlow(client_id=client_id, client_secret=client_secret)

        try:
            token = auth.get_token()
        except RuntimeError as e:
            raise LoginError(error_type=GenerateUserAccessTokenError(str(e)))

        return token
