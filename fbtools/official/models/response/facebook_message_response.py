"""Response object for facebook message."""

from pydantic import BaseModel


class FacebookMessageResponse(BaseModel):
    """FacebookMessageResponse object."""

    recipient_id: str
    message_id: str
