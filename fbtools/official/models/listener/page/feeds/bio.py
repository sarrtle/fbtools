"""Bio field webhook.

Sample data:
{
    "entry": [
        {
            "id": "0",
            "time": 1740764080,
            "changes": [ # Bio field starts here
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
    value: None = None
