"""Model object for webhook parameters."""

from typing import cast
from fastapi import Query
from pydantic import BaseModel


class WebhookParams(BaseModel):
    """Parameters for webhook."""

    mode: str = cast(str, Query(..., alias="hub.mode"))
    token: str = cast(str, Query(..., alias="hub.verify_token"))
    challenge: str = cast(str, Query(..., alias="hub.challenge"))
