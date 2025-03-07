"""Dispatcher decorator to dispatch events."""

from typing import Callable, TypeVar, cast
from collections.abc import Awaitable

import asyncio


class BaseEvent:
    """The base object for all events.

    To be imported and inherited by event objects.
    """

    pass


# ================ Dispatcher Decorator ================

# create a type variable for events that are subclasses of BaseEvent
Event = TypeVar("Event", bound=BaseEvent)

# A handler is a callable that takes an event of type EventType and returns an Awaitable[None]
EventHandler = Callable[[Event], Awaitable[None]]


class EventDispatcher:
    """EventDispatcher object."""

    def __init__(self) -> None:
        """Initialize EventDispatcher."""
        self._handlers: dict[
            type[BaseEvent], list[Callable[[BaseEvent], Awaitable[None]]]
        ] = {}
        pass

    def handle(
        self, event_type: type[Event]
    ) -> Callable[[EventHandler[Event]], EventHandler[Event]]:
        """Register a handler for a given event type."""

        def decorator(func: EventHandler[Event]) -> EventHandler[Event]:
            # cast the handler to one that accepts BaseEvent for storage
            self._handlers.setdefault(event_type, []).append(
                cast(Callable[[BaseEvent], Awaitable[None]], func)
            )
            return func

        return decorator

    async def invoke(self, event: BaseEvent):
        """Invoke all handlers for a given event type."""
        handlers = self._handlers.get(type(event), [])
        tasks: list[Awaitable[None]] = []
        for handler in handlers:
            tasks.append(handler(event))

        if tasks:
            await asyncio.gather(*tasks)


# run importable dispatcher
fbtools_dispatcher = EventDispatcher()
