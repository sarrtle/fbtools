"""Events of official fbgraph."""

from fbtools.official.events.dispatcher import BaseEvent


class onNewPost(BaseEvent):
    """Sends a notification when you created a post."""


class onPostReaction(BaseEvent):
    """Sends a notification when someone react to your post."""


class onComment(BaseEvent):
    """Sends a notification when someone commented to your post."""


class onCommentReaction(BaseEvent):
    """Sends a notification when someone react to your comment."""


class onMessage(BaseEvent):
    """Sends a notification when someone messages your page."""


class onMessageReaction(BaseEvent):
    """Sends a notification when someone react to your message."""
