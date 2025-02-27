"""The base page object to all fields."""

from typing import Literal
from pydantic import BaseModel

from fbtools.official.models.page.messages import Messages


class Page(BaseModel):
    """The page object from webhook data.

    This is the base page object to all fields.
    """

    object: Literal["page"]
    entry: list[Messages]
