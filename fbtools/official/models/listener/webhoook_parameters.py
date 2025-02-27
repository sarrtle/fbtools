"""Model object for webhook parameters."""

from fastapi import Query
from pydantic import BaseModel


class WebhookParams(BaseModel):
    """Parameters for webhook."""

    mode: str = Query(..., alias="hub.mode")
    token: str = Query(..., alias="hub.verify_token")
    challenge: str = Query(..., alias="hub.challenge")
