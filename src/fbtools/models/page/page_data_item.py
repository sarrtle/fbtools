"""Validation of page data items."""

from pydantic import BaseModel


class PageDataItem(BaseModel):
    """Page data item."""

    access_token: str
    category: str
    name: str
    id: str
