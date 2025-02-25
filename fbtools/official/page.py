"""Page object of Facebook node."""

from typing import override
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
        self.tasks: list[str] = page_data_item.tasks
        self.access_token: str = page_data_item.access_token

        # objects
        self.session: AsyncClient = AsyncClient(base_url="https://graph.facebook.com/")

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

    @override
    def __repr__(self):
        return f"Page(name={self.name}, category={self.category}, tasks={self.tasks}, access_token={self.access_token[:5]}...)"
