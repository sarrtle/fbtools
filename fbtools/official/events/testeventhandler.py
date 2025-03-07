"""Testing the events."""

from fbtools.official.events.testmodel.testeventobject import TestEvent
from fbtools.official.events.dispatcher import fbtools_dispatcher


@fbtools_dispatcher.handle(TestEvent)
async def ping_test_event(event: TestEvent) -> None:
    """Ping test event."""
    event.ping()
