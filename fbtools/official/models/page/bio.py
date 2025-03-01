"""Bio field webhook.

Sample data:
{
    "entry": [
        {
            "id": "0",
            "time": 1740764080,
            "changes": [
                {
                    "field": "bio"
                }
            ]
        }
    ],
    "object": "page"
}
"""

from typing import Literal
from pydantic import BaseModel


class BioField(BaseModel):
    """Bio field data."""

    field: Literal["bio"]


class Bio(BaseModel):
    """Bio field data."""

    id: str
    time: int
    changes: list[BioField]
