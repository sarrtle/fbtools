"""Picture webhook data.

Will notify you if you change your page
profile picture.
"""

from typing import Literal
from pydantic import BaseModel


class PictureField(BaseModel):
    """PictureField data."""

    field: Literal["picture"]
    value: None = None
