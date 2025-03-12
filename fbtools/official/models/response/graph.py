"""Response objects for Facebook Graph API."""

from pydantic import BaseModel


class SuccessResponse(BaseModel):
    """Success response from Facebook Graph API."""

    success: bool
