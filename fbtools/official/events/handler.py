"""Handle event data into objects."""

import asyncio
from httpx import AsyncClient
from fbtools.official.events.dispatcher import official_event_dispatcher
from fbtools.official.events.models import onNewPost
from fbtools.official.models.listener.page.feeds.feed import (
    FeedNewPost,
    FeedNewPostWithManyPhotos,
    FeedNewPostWithPhoto,
    FeedNewPostWithVideo,
)
from fbtools.official.models.listener.page.page import Page, PageEntry

from fbtools.official.models.page.post import FacebookPost


def handle_feed_event(page_object: Page, access_token: str, session: AsyncClient):
    """Handle new post event."""
    if not isinstance(page_object.entry[0], PageEntry):
        return

    for change in page_object.entry[0].changes:

        # For new post event
        if (
            isinstance(change.value, FeedNewPost)
            or isinstance(change.value, FeedNewPostWithPhoto)
            or isinstance(change.value, FeedNewPostWithManyPhotos)
            or isinstance(change.value, FeedNewPostWithVideo)
        ):
            feed_object = change.value
            post_object = FacebookPost(
                post_id=feed_object.post_id, access_token=access_token, session=session
            )
            new_post_event = onNewPost(
                post_object=post_object,
                message=feed_object.message,
                post_id=feed_object.post_id,
                created_time=feed_object.created_time,
            )

            asyncio.create_task(official_event_dispatcher.invoke(event=new_post_event))
