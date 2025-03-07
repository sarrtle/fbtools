"""Test event."""

from fbtools.official.events.dispatcher import BaseEvent


class TestEvent(BaseEvent):
    """Test event."""

    def __init__(self):
        """Initialize TestEvent."""
        pass

    def ping(self):
        """Ping."""
        print("pong")
