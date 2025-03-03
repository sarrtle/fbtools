"""Messaging postbacks content."""

from typing import Literal
from pydantic import BaseModel


class MessagingPostbackContent(BaseModel):
    """Messaging postback content."""

    mid: str
    title: str
    payload: str
    referral: "PostbackReferral"


class PostbackReferral(BaseModel):
    """Postback referral data."""

    ref: str
    source: str
    type: Literal["OPEN_THREAD"]


MessagingPostbackContent.model_rebuild()
