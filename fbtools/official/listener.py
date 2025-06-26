"""Object listener for handling webhook events.

Webhook events are those from messenger, page events and even
user events that are connected or used your apps.
"""

from hashlib import blake2b
from typing import Annotated, Callable
from fastapi import FastAPI, HTTPException, Query, Request, status

from concurrent.futures import ThreadPoolExecutor

from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, PlainTextResponse

from fbtools.official.models.listener.webhoook_parameters import (
    WebhookParams,
)


import uvicorn

from fbtools.official.models.listener.page.feeds.feed import FeedNewPostWithPhoto
from fbtools.official.models.listener.page.page import Page, PageEntry

import json

from cachetools import FIFOCache


class Listener:
    """Listener object.

    Attributes:
        verify_token: The verify token for webhook events.
        app: The existing FastAPI app. Ignore if you are using listener as a standalone.
        host: The host for the FastAPI server.
        port: The port for the FastAPI server.
        cache: The cache for webhook events.

        debug_webhook: Enable disable debugging of webhoook payload.

    """

    def __init__(
        self,
        verify_token: str,
        app: FastAPI | None,
        host: str,
        port: int,
        debug_webhook: bool = False,
    ) -> None:
        """Initialize Listener.

        Args:
            verify_token: The verify token for webhook events.
            app: The existing FastAPI app. Ignore if you are using listener as a standalone.
            host: The host for the FastAPI server.
            port: The port for the FastAPI server.
            debug_webhook: Enable disable debugging of webhoook payload.

        """
        # attributes
        self.verify_token: str = verify_token
        self.app: FastAPI = app or FastAPI()
        self.host: str = host
        self.port: int = port
        self.debug_webhook: bool = debug_webhook
        self.cache: FIFOCache[str, bool] = FIFOCache(maxsize=1024)

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
        async def handle_webhook_events(page_object: Page, request: Request):

            # handle edited event for profile picture when
            # someone is commenting to the profile picture post
            # the webhook keeps sending edited event with no changes
            # unless it is a `link`
            if page_object.object == "page":
                entry_type = page_object.entry[0]
                if isinstance(entry_type, PageEntry):
                    feed_model = entry_type.changes[0].value
                    if (
                        isinstance(feed_model, FeedNewPostWithPhoto)
                        and feed_model.verb == "edited"
                    ):
                        data = feed_model.model_dump()
                        # remove the link url since that is the major
                        # changes of this webhook event that sends verb:edited
                        # update
                        del data["link"]

                        # remove the `from_` to validate only the new
                        # recent changes
                        del data["from_"]

                        # convert data to string and create hash key
                        data = json.dumps(data)
                        key = blake2b(
                            data.encode(encoding="utf-8"), digest_size=16
                        ).hexdigest()
                        if self.cache.get(key):
                            return
                        self.cache[key] = True

            # print("--- RAW DATA ---")
            # print(json.dumps(await request.json(), indent=4))
            await self._handle_page_events(page_object)

        # async def handle_webhook_events(request: Request):
        #     print(dumps(await request.json(), indent=4))
        #     print()
        #     print("---")
        #     print()

        # handle error for debugging response
        async def validation_exception_handler(request: Request, exc: Exception):
            if isinstance(exc, RequestValidationError):
                print("Invalid payload:")
                print(json.dumps(await request.json(), indent=4))
                print("---")

                return JSONResponse(status_code=422, content={"detail": exc.errors()})
            raise exc

        self.app.add_api_route("/webhook", endpoint=verify_webhook, methods=["GET"])
        self.app.add_api_route(
            "/webhook", endpoint=handle_webhook_events, methods=["POST"]
        )

        if self.debug_webhook:
            self.app.add_exception_handler(
                RequestValidationError, validation_exception_handler
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

    # PRIVATE methods
    # -------------------------
    # handling events
    async def _handle_page_events(self, page_object: Page) -> None:
        print(page_object.object)
        print(page_object.entry)
