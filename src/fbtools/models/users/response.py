"""All response models for User Node."""

from pydantic import BaseModel


class LoginAsTokenResponse(BaseModel):
    """Response for login with access token."""

    short_name: str
    id: str
