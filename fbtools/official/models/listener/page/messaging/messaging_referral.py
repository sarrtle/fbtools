"""Messaging referral content."""

from typing import Literal
from pydantic import BaseModel


class MessagingReferralContent(BaseModel):
    """Messaging referral content."""

    ref: str
    source: str
    type: Literal["OPEN_THREAD"]
    ads_context_data: "AdsContextData"


class AdsContextData(BaseModel):
    """Ads context data."""

    ad_title: str
    photo_url: str
    video_url: str
    post_id: str
    product_id: str


MessagingReferralContent.model_rebuild()
