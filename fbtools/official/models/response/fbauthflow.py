"""All objects for fb auth flow."""

from pydantic import BaseModel


class FbAuthResponse(BaseModel):
    """Response from fb auth flow."""

    access_token: str
    message: str
