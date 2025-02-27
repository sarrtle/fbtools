"""Object listener for handling webhook events.

Webhook events are those from messenger, page events and even
user events that are connected or used your apps.
"""

from typing import Annotated, Callable
from fastapi import FastAPI, HTTPException, Query, Request, status

from concurrent.futures import ThreadPoolExecutor

from fastapi.responses import PlainTextResponse

from fbtools.official.models.listener.webhoook_parameters import (
    WebhookParams,
)

from json import dumps

import uvicorn


class Listener:
    """Listener object.

    Attributes:
        verify_token: The verify token for webhook events.
        app: The existing FastAPI app. Ignore if you are using listener as a standalone.
        host: The host for the FastAPI server.
        port: The port for the FastAPI server.

    """

    def __init__(
        self, verify_token: str, app: FastAPI | None, host: str, port: int
    ) -> None:
        """Initialize Listener.

        Args:
            verify_token: The verify token for webhook events.
            app: The existing FastAPI app. Ignore if you are using listener as a standalone.
            host: The host for the FastAPI server.
            port: The port for the FastAPI server.

        """
        # attributes
        self.verify_token: str = verify_token
        self.app: FastAPI = app or FastAPI()
        self.host: str = host
        self.port: int = port

        # important private attributes
        self._callback: Callable[[], None] | None = None
        self._executor: ThreadPoolExecutor = ThreadPoolExecutor(
            max_workers=200, thread_name_prefix="listener"
        )

        # checkers
        self._is_internal_app: bool = app is None

        # set up functions
        self._setup_routes()

    def _setup_routes(self):
        """Set up the routes of webhook."""

        # handling verification
        async def verify_webhook(webhook_params: Annotated[WebhookParams, Query()]):
            if (
                webhook_params.mode != "subscribe"
                and webhook_params.token != self.verify_token
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden"
                )

            return PlainTextResponse(webhook_params.challenge)

        # handling events
        # async def handle_webhook_events(payload: UserWebhookBody | PageWebhookBody):
        #     print(payload.object)
        #     raise NotImplementedError

        async def handle_webhook_events(request: Request):
            print(dumps(await request.json(), indent=4))
            print()
            print("---")
            print()

        self.app.add_api_route("/webhook", endpoint=verify_webhook, methods=["GET"])
        self.app.add_api_route(
            "/webhook", endpoint=handle_webhook_events, methods=["POST"]
        )

    def set_callback(self, callback: Callable[[], None]):
        """Set the callback function for the listener.

        Args:
            callback: The callback function for the listener.

        """
        self._callback = callback

    def start(self):
        """Start the listener only if it is an internal app."""
        if not self._is_internal_app:
            raise RuntimeError(
                "Listener is not an internal app. Consider add your FastAPI `app` into the listener's parameter."
            )

        # start the listener
        uvicorn.run(self.app, host=self.host, port=self.port)
