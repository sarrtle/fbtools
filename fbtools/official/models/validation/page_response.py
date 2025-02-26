"""All validation objects for official APIs."""

from pydantic import BaseModel


# Show pages list response validation
class PageDataItem(BaseModel):
    """Data item from response."""

    access_token: str
    category: str
    name: str
    id: str


class CursorItem(BaseModel):
    """Cursor item from paging."""

    before: str
    after: str


class PagingItem(BaseModel):
    """Paging item from response."""

    cursors: CursorItem


class PageResponse(BaseModel):
    """Page response validation."""

    data: list[PageDataItem]
    paging: PagingItem
