"""Post and video id response."""

from pydantic import BaseModel


class FeedIdResponse(BaseModel):
    """Feed id response model."""

    post_id: str
    id: str
