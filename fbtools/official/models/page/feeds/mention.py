"""Mention webhook field.

This is when someone mentions the page in a post or comment.

Warning:
    Needs more investigation, the docs seems different from the actual data.
    And unclear or incomplete.

Sample data:
{
    "entry": [
        {
            "id": "0",
            "time": 1740909637,
            "changes": [ # FacebookMentionField starts here
                {
                    "field": "mention",
                    "value": {
                        "post_id": "44444444_444444444",
                        "sender_name": "Example Name",
                        "item": "post",
                        "sender_id": "44444444",
                        "verb": "add"
                    }
                }
            ]
        }
    ],
    "object": "page"
}

"""

from typing import Literal
from pydantic import BaseModel


class MentionField(BaseModel):
    """Values of mention field data."""

    field: Literal["mention"]
    value: "MentionData"


class MentionData(BaseModel):
    """Mention object data.

    Attributes:
        post_id: The id of the post that mentioned the page.
        sender_name: The name of the person who mentioned the page.
        item: What type of feed is it.
        sender_id: The id of the person who mentioned the page.
        verb: The action of the mention.

    """

    post_id: str
    sender_name: str
    item: Literal["post"]
    sender_id: str
    verb: Literal["add"]


MentionField.model_rebuild()
