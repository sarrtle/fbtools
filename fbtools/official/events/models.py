"""Events of official fbgraph."""

from fbtools.official.events.dispatcher import BaseEvent
from fbtools.official.models.listener.page.feeds.feed import REACTION_TYPES
from fbtools.official.models.page.message import FacebookMessage
from fbtools.official.models.page.post import FacebookPost
from fbtools.official.models.page.comment import FacebookComment
from fbtools.official.page import Page


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
        with_attachment: bool,
        created_time: int,
        page: Page,
    ):
        """Initialize the event.

        Args:
            post_object: the Facebook post object.
            message: The caption of the post.
            post_id: The id of the post.
            with_attachment: True if the post has an attachment.
            created_time: The time of the post creation.
            page: The Facebook page object.

        """
        self.post_object: FacebookPost = post_object
        self.message: str | None = message
        self.post_id: str = post_id
        self.created_time: int = created_time
        self.page: Page = page


class onPostReaction(BaseEvent):
    """Sends a notification when someone react to your post.

    Attributes:
        from_id: The id of the person who react.
        from_name: The name of the person who react.
        post_id: The id of the post.
        post_object: The Facebook post object.
        timestamp: The timestamp of the reaction.
        reaction_type: The type of the reaction.

    """

    def __init__(
        self,
        from_id: str,
        from_name: str,
        post_id: str,
        post_object: FacebookPost,
        timestamp: int,
        reaction_type: REACTION_TYPES,
        page: Page,
    ):
        """Initialize onPostReaction.

        Args:
            from_id: The id of the person who react.
            from_name: The name of the person who react.
            post_id: The id of the post.
            post_object: The Facebook post object.
            timestamp: The timestamp of the reaction.
            reaction_type: The type of the reaction.
            page: The Facebook page object.

        """
        self.from_id: str = from_id
        self.from_name: str = from_name
        self.post_id: str = post_id
        self.post_object: FacebookPost = post_object
        self.timestamp: int = timestamp
        self.reaction_type: REACTION_TYPES = reaction_type
        self.page: Page = page


class onComment(BaseEvent):
    """Sends a notification when someone commented to your post."""

    def __init__(
        self,
        from_id: str,
        from_name: str,
        text: str | None,
        comment_id: str,
        comment_object: FacebookComment,
        with_attachment: bool,
        created_time: int,
        page: Page,
    ):
        """Initialize onComment.

        Args:
            from_id: The id of the person who commented.
            from_name: The name of the person who commented.
            post_object: the Facebook post object.
            text: The caption of the post.
            comment_id: The id of the comment.
            comment_object: the Facebook comment object.
            with_attachment: True if the post has an attachment.
            created_time: The time of the post creation.
            page: The Facebook page object.

        """
        self.from_id: str = from_id
        self.from_name: str = from_name
        self.text: str | None = text
        self.comment_id: str = comment_id
        self.comment_object: FacebookComment = comment_object
        self.with_attachment: bool = with_attachment
        self.created_time: int = created_time
        self.page: Page = page


class onCommentReaction(BaseEvent):
    """Sends a notification when someone react to your comment."""

    def __init__(
        self,
        from_id: str,
        from_name: str,
        comment_id: str,
        comment_object: FacebookComment,
        timestamp: int,
        reaction_type: REACTION_TYPES,
        page: Page,
    ):
        """Initialize onCommentReaction.

        Args:
            from_id: The id of the person who react.
            from_name: The name of the person who react.
            comment_id: The id of the comment.
            comment_object: The Facebook comment object.
            timestamp: The timestamp of the reaction.
            reaction_type: The type of the reaction.
            page: The Facebook page object.

        """
        self.from_id: str = from_id
        self.from_name: str = from_name
        self.comment_id: str = comment_id
        self.comment_object: FacebookComment = comment_object
        self.timestamp: int = timestamp
        self.reaction_type: REACTION_TYPES = reaction_type
        self.page: Page = page


class onMessage(BaseEvent):
    """Sends a notification when someone messages your page."""

    def __init__(self, message_object: FacebookMessage, page: Page):
        """Initialize onMessage.

        Args:
            message_object: The Facebook message object.
            page: The Facebook page object.

        """
        self.message_object: FacebookMessage = message_object
        self.page: Page = page


class onMessageReaction(BaseEvent):
    """Sends a notification when someone react to your message."""

    def __init__(
        self,
        emoji: str | None,
        reaction_description: str | None,
        message_object: FacebookMessage,
        page: Page,
    ):
        """Initialize onMessageReaction.

        Args:
            emoji: The emoji of the reaction.
            reaction_description: The description of the reaction.
            message_object: The Facebook message object.
            page: The Facebook page object.

        """
        self.emoji: str | None = emoji
        self.reaction_description: str | None = reaction_description
        self.message_object: FacebookMessage = message_object
        self.page: Page = page
