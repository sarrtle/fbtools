"""Page object of Facebook node."""

from httpx import AsyncClient

from fbtools.official.exceptions import LoginError, PageValidationError


class Page:
    """Page object of Facebook node."""

    def __init__(self):
        """Initialize Page."""
        # attributes
        self.access_token: str | None = None

        # objects
        self.session: AsyncClient = AsyncClient(base_url="https://graph.facebook.com/")

    # login methods
    async def login_with_access_token(
        self, page_access_token: str, skip_validation: bool = False
    ):
        """Directly using your generated access token.

        Args:
            page_access_token: The page access token created from facebook developer tools.
            skip_validation: Skip validation of the access token.

        """
        # need validation of the token before use
        if not skip_validation:
            # global_brand_page_name name is for the page only
            params = {
                "access_token": page_access_token,
                "fields": "global_brand_page_name",
            }
            response = await self.session.get("me", params=params)

            if response.status_code != 200:
                raise LoginError(error_type=PageValidationError(response.text))

        self.access_token = page_access_token
