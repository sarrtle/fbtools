"""The base page object to all fields."""

from typing import Literal
from pydantic import BaseModel, Field

from fbtools.official.models.page.feeds.bio import BioField
from fbtools.official.models.page.feeds.feed import FacebookFeed
from fbtools.official.models.page.feeds.mention import MentionField
from fbtools.official.models.page.feeds.name import NameField
from fbtools.official.models.page.feeds.picture import PictureField
from fbtools.official.models.page.messaging.message import Message

# types of feeds
FeedTypes = BioField | FacebookFeed | MentionField | NameField | PictureField


class Page(BaseModel):
    """The page object from webhook data.

    This is the base page object to all fields.
    """

    object: Literal["page"]
    entry: list["PageEntry | MessageEntry"]


class PageEntry(BaseModel):
    """The page entry object from webhook data.

    This is the base page entry object to all fields.

    Attributes:
        id: The id of the webhook.
        time: The time webhook received.
        changes: What kind of event happened. List of fields.

    """

    id: str
    time: int
    changes: list[FeedTypes] = Field(..., discriminator="field")


class MessageEntry(BaseModel):
    """Messages entry data.

    This is inside entry key that contains list
    of dictionary. Just this once, it is different
    from page entries where the webhook events are
    for the page not messages.

    Attributes:
        time: The time of the message.
        id: The id of the message.
        messaging: The messaging object data.

    """

    time: int
    id: str
    messages: list[Message] = Field(..., alias="messaging")


Page.model_rebuild()
