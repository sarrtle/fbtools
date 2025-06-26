"""Events of official fbgraph."""

from fbtools.official.events.dispatcher import BaseEvent
from fbtools.official.models.page.post import FacebookPost


class onNewPost(BaseEvent):
    """Sends a notification when you created a post.

    Notes:
        post_object needs to be initialized in order to access some data
        got from additional API request.

    Attributes:
        post_object: the Facebook post object.
        message: The caption of the post.
        post_id: The id of the post.
        created_time: The time of the post creation.

    """

    def __init__(
        self,
        post_object: FacebookPost,
        message: str | None,
        post_id: str,
        created_time: int,
    ):
        """Initialize the event.

        Args:
            post_object: the Facebook post object.
            message: The caption of the post.
            post_id: The id of the post.
            created_time: The time of the post creation.

        """
        self.post: FacebookPost = post_object
        self.message: str | None = message
        self.post_id: str = post_id
        self.created_time: int = created_time


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
