"""Handle event data into objects."""

import asyncio
from typing import cast
from fbtools.official.events.dispatcher import official_event_dispatcher
from fbtools.official.events.models import (
    onCommentReaction,
    onMessage,
    onMessageReaction,
    onNewPost,
    onPostReaction,
)
from fbtools.official.models.listener.page.feeds.feed import (
    FeedComment,
    FeedCommentWithPhoto,
    FeedCommentWithVideo,
    FeedNewPost,
    FeedNewPostWithManyPhotos,
    FeedNewPostWithPhoto,
    FeedNewPostWithVideo,
    FeedNewReactionOnComment,
    FeedNewReactionOnPost,
)
from fbtools.official.models.listener.page.messaging.message_content import (
    MessageContent,
)
from fbtools.official.models.listener.page.messaging.message_reaction import (
    MessageReactionContent,
)
from fbtools.official.models.listener.page.page import MessageEntry, Page, PageEntry

from fbtools.official.models.page.comment import FacebookComment
from fbtools.official.models.page.message import FacebookMessage
from fbtools.official.models.page.post import FacebookPost

from fbtools.official.page import Page as FacebookPage


def handle_feed_event(webhook_page_object: Page, page_object: FacebookPage):
    """Handle new post event."""
    # we already know that this is a page entry
    # because we just checked it outside.
    page_entry = cast(PageEntry, webhook_page_object.entry[0])

    # get current running loop
    current_loop = asyncio.get_running_loop()

    # looping through this even we know that there are only
    # 1 changes but just to be sure if ever Facebook changes
    # their style, so all events will be handled.
    for change in page_entry.changes:

        # For new post event event
        if (
            isinstance(change.value, FeedNewPost)
            or isinstance(change.value, FeedNewPostWithPhoto)
            or isinstance(change.value, FeedNewPostWithManyPhotos)
            or isinstance(change.value, FeedNewPostWithVideo)
        ):
            feed_object = change.value
            post_object = FacebookPost(
                post_id=feed_object.post_id,
                access_token=page_object.access_token,
                session=page_object.session,
            )

            # check attachments
            with_attachment = False
            if (
                isinstance(feed_object, FeedNewPostWithPhoto)
                or isinstance(feed_object, FeedNewPostWithManyPhotos)
                or isinstance(feed_object, FeedNewPostWithVideo)
            ):
                with_attachment = True

            new_post_event = onNewPost(
                post_object=post_object,
                message=feed_object.message,
                post_id=feed_object.post_id,
                with_attachment=with_attachment,
                created_time=feed_object.created_time,
                page=page_object,
            )

            current_loop.create_task(
                official_event_dispatcher.invoke(event=new_post_event)
            )

        # for reaction on post event
        if isinstance(change.value, FeedNewReactionOnPost):
            feed_object = change.value
            if feed_object.verb == "add":
                reaction_type = feed_object.reaction_type
                from_id = feed_object.from_.id
                from_name = feed_object.from_.name
                post_id = feed_object.post_id
                post_object = FacebookPost(
                    post_id=post_id,
                    access_token=page_object.access_token,
                    session=page_object.session,
                )
                new_reaction_event = onPostReaction(
                    from_id=from_id,
                    from_name=from_name,
                    post_id=post_id,
                    post_object=post_object,
                    timestamp=feed_object.created_time,
                    reaction_type=reaction_type,
                    page=page_object,
                )

                current_loop.create_task(
                    official_event_dispatcher.invoke(event=new_reaction_event)
                )
            # TODO: handle reaction edit and remove

        # on comment event
        if (
            isinstance(change.value, FeedComment)
            or isinstance(change.value, FeedCommentWithPhoto)
            or isinstance(change.value, FeedCommentWithVideo)
        ):
            feed_object = change.value
            if feed_object.verb == "add":
                from_id = feed_object.from_.id
                from_name = feed_object.from_.name
                post_id = feed_object.post_id

                post_object = FacebookPost(
                    post_id=post_id,
                    access_token=page_object.access_token,
                    session=page_object.session,
                )

                comment_object = FacebookComment(
                    comment_id=feed_object.comment_id,
                    access_token=page_object.access_token,
                    session=page_object.session,
                    parent_comment=None,  # TOOD: add parent comment if reply
                    parent_post=post_object,
                )

                # check attachments
                with_attachment = False
                if isinstance(feed_object, FeedCommentWithPhoto) or isinstance(
                    feed_object, FeedCommentWithVideo
                ):
                    with_attachment = True

        if isinstance(change.value, FeedNewReactionOnComment):
            feed_object = change.value
            if feed_object.verb == "add":
                reaction_type = feed_object.reaction_type
                from_id = feed_object.from_.id
                from_name = feed_object.from_.name
                post_id = feed_object.post_id
                comment_id = feed_object.comment_id
                post_object = FacebookPost(
                    post_id=post_id,
                    access_token=page_object.access_token,
                    session=page_object.session,
                )
                comment_object = FacebookComment(
                    comment_id=comment_id,
                    access_token=page_object.access_token,
                    session=page_object.session,
                    # TOOD: add parent comment if reply
                    #       or if there some indicator to know
                    #       that this is a comment reply
                    parent_comment=None,
                    parent_post=post_object,
                )

                new_reaction_event = onCommentReaction(
                    from_id=from_id,
                    from_name=from_name,
                    comment_id=comment_id,
                    comment_object=comment_object,
                    timestamp=feed_object.created_time,
                    reaction_type=feed_object.reaction_type,
                    page=page_object,
                )

                current_loop.create_task(
                    official_event_dispatcher.invoke(event=new_reaction_event)
                )


def handle_message_event(webhook_page_object: Page, page_object: FacebookPage):
    """Handle message events."""
    message_entry = cast(MessageEntry, webhook_page_object.entry[0])

    current_loop = asyncio.get_running_loop()

    for message in message_entry.messages:
        sender = message.sender.id
        recipient = message.recipient.id
        timestamp = message.timestamp
        message_type = message.message_type

        # on message event
        if isinstance(message_type, MessageContent):
            message_object = FacebookMessage(
                sender=sender,
                recipient=recipient,
                text=message_type.text,
                timestamp=timestamp,
                message_id=message_type.mid,
                attachments=message_type.attachments or [],
                session=page_object.session,
                access_token=page_object.access_token,
            )

            new_message_event = onMessage(
                message_object=message_object,
                page=page_object,
            )

            current_loop.create_task(
                official_event_dispatcher.invoke(event=new_message_event)
            )

        # on message react
        if isinstance(message_type, MessageReactionContent):
            message_object = FacebookMessage(
                sender=sender,
                recipient=recipient,
                text=None,
                timestamp=timestamp,
                message_id=message_type.mid,
                attachments=[],
                session=page_object.session,
                access_token=page_object.access_token,
            )

            new_reaction_event = onMessageReaction(
                emoji=message_type.emoji,
                reaction_description=message_type.reaction,
                message_object=message_object,
                page=page_object,
            )

            current_loop.create_task(
                official_event_dispatcher.invoke(event=new_reaction_event)
            )

        # TODO:
        # message edit
        # message react
        # message read
        # message postback
