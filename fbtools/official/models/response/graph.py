"""Response objects for Facebook Graph API."""

from datetime import datetime
from typing import Literal
from pydantic import BaseModel


class SuccessResponse(BaseModel):
    """Success response from Facebook Graph API."""

    success: bool


class FacebookPostResponse(BaseModel):
    """Post response from Facebook Graph API."""

    id: str
    message: str | None
    status_type: Literal["added_photos", "added_video", "mobile_status_update"]
    story: str | None
    created_time: datetime
