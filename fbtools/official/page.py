"""Page object of Facebook node."""

from typing import Literal, override
from httpx import AsyncClient

from fbtools.official.exceptions import PageValidationError
from fbtools.official.models.validation.page_response import PageDataItem


class Page:
    """Page object of Facebook node.

    Attributes:
        name: The page name.
        category: The page category.
        tasks: The page tasks.
        access_token: The page access token.
        session: httpx async session of this node.

    """

    def __init__(self, page_data_item: PageDataItem):
        """Initialize Page.

        Args:
            page_data_item: The page data item from response.

        """
        # attributes
        self.name: str = page_data_item.name
        self.category: str = page_data_item.category
        self.access_token: str = page_data_item.access_token

        # objects
        self.session: AsyncClient = self.create_session()

    @classmethod
    def create_session(cls):
        """Create httpx async session of this node."""
        return AsyncClient(base_url="https://graph.facebook.com/")

    @classmethod
    async def from_access_token(
        cls, page_access_token: str, user_id: str | Literal["me"] = "me"
    ) -> "Page":
        """Create a page node from access token.

        Since the orignal initial setup requires page data item
        from the page response of getting the page data. An
        access token will request the page data and create the
        page data item.

        Args:
            page_access_token: The page access token.
            user_id: The user id or "me". The "me" is used on dev mode.

        Returns:
            The page node.

        Raises:
            ValidationError: If something went wrong during validation of api response.

        """
        # request page data from official api with access token
        params = {
            "access_token": page_access_token,
            "fields": "id,name,category, access_token",
        }
        response = await cls.create_session().get(f"{user_id}", params=params)

        # validate data
        page_data_item = PageDataItem.model_validate(response.json())

        # add data to Page node
        return Page(page_data_item=page_data_item)

    # validate page access token
    async def validate_access_token(self):
        """Will check if page access token is valid.

        Raises:
            PageValidationError: If page access token is invalid.

        """
        # global_brand_page_name name is for the page only
        params = {
            "access_token": self.access_token,
            "fields": "global_brand_page_name",
        }
        response = await self.session.get("me", params=params)

        if response.status_code != 200:
            raise PageValidationError(response.text)

    def save_page_access_token(
        self, page_access_token: str, filepath: str = "page_token.txt"
    ):
        """Save page access token.

        Args:
            page_access_token: The page access token.
            filepath: The file path to save the access token.

        """
        with open(filepath, "w") as f:
            f.write(page_access_token)

    @override
    def __repr__(self):
        return f"Page(name={self.name}, category={self.category}, access_token={self.access_token[:5]}...)"
