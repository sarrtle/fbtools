"""Dispatcher decorator to dispatch events."""

from operator import itemgetter
from typing import Callable, TypeVar, TypedDict
from collections.abc import Coroutine

import asyncio


class BaseEvent:
    """The base object for all events.

    To be imported and inherited by event objects.
    """

    pass


Event = TypeVar("Event", bound=BaseEvent)
Handler = Callable[..., Coroutine[None, None, None]]


class HandlerDict(TypedDict):
    """HandlerDict object."""

    priority: int
    handlers: list[Handler]


HandlerType = dict[type[BaseEvent], list[HandlerDict]]


class EventDispatcher:
    """EventDispatcher object."""

    def __init__(self):
        """Initialize the event dispatcher."""
        self.handlers: HandlerType = {}

    def register(self, event: type[BaseEvent], priority: int = 0):
        """Register the function with an event handler.

        Events are event object to be use when the listener is receiving
        webhook data.

        Priority is the order of the event handlers to be invoked if there are
        multiple subscribers into one event. Same value of priority will run
        the handlers at the same time.

        Args:
            event: The event to register.
            priority: The priority of the event handler.

        """

        def decorator(func: Callable[[Event], Coroutine[None, None, None]]):
            # algorithm time
            event_data = self.handlers.setdefault(event, [])

            # assign priority
            if event_data:
                with_priority = False
                for e in event_data:
                    if e.get("priority") == priority:
                        e.get("handlers").append(func)
                        with_priority = True
                        continue
                if not with_priority:
                    event_data.append({"priority": priority, "handlers": [func]})

            else:
                event_data.append({"priority": priority, "handlers": [func]})
            # Sort it now on register to avoid overhead on invocation
            event_data.sort(key=itemgetter("priority"))
            # or
            # event_data.sort(key=lambda x: x["priority"])

            return func

        return decorator

    async def invoke(self, event: type[BaseEvent]):
        """Invoke the given event."""
        handler_list = self.handlers.get(event, [])

        # sequential run one by one
        # on priority but if there are the same
        # priority, then it will run at the same time
        # asynchronously
        for handler in handler_list:
            handlers: list[Handler] = handler.get("handlers")
            tasks: list[asyncio.Task[None]] = []
            for task in handlers:
                tasks.append(asyncio.create_task(task(event)))
            _ = await asyncio.gather(*tasks)


official_event_dispatcher = EventDispatcher()
