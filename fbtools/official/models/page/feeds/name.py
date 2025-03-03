"""Name webhook data.

Will notify you if you change the name of
your page.
"""

from typing import Literal
from pydantic import BaseModel


class NameField(BaseModel):
    """NameField data."""

    field: Literal["name"]
    value: str
