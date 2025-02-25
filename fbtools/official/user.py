"""User object Facebook of node."""

from typing import Literal
from httpx import AsyncClient

from fbtools.official.exceptions import (
    GenerateUserAccessTokenError,
    LoginError,
    UserValidationError,
)
from fbtools.official.models.validation.page_response import PageResponse
from fbtools.utilities.fbauthflow import FacebookAuthFlow

from fbtools.official.page import Page


class User:
    """User Node of Facebook.

    All user related APIs will be here.

    Attributes:
        user_id: The user id or "me". The "me" is used on dev mode.
        access_token: The user access token created from facebook developer tools.
        session: An asynchronous httpx session of this node.

    """

    def __init__(self, user_id: str | Literal["me"] = "me"):
        """Initialize User.

        Args:
            user_id: The user id or "me". The "me" is used on dev mode.

        """
        # attributes
        self.user_id: str = user_id if user_id != "me" else "me"
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
            response = await self.session.get(self.user_id, params=params)

            if response.status_code != 200:
                raise LoginError(error_type=UserValidationError(response.text))

        self.access_token = user_access_token

    async def generate_access_token(self, client_id: str, client_secret: str) -> None:
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

        self.access_token = token
        print("Generated access token:", self.access_token)

    def save_user_access_token(
        self, user_access_token: str, filepath: str = "access_token.txt"
    ) -> None:
        """Save user access token to local file.

        Args:
            user_access_token: The user access token created from facebook login.
            filepath: The file path to save the access token. Default on root folder.

        """
        with open(filepath, "w") as f:
            f.write(user_access_token)

    async def get_pages(self) -> list[Page]:
        """Show pages available from the user.

        Returns:
            A list of Page node.

        Raises:
            ValidationError: If something went wrong during validation of api response.

        """
        # to return
        pages: list[Page] = []

        # request page data from official api
        params = {"access_token": self.access_token}
        response = await self.session.get(f"{self.user_id}/accounts", params=params)

        # validate data
        page_response = PageResponse.model_validate(response.json())

        # add data to Page node
        for page in page_response.data:
            pages.append(Page(page_data_item=page))

        return pages
