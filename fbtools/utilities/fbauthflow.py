"""Will generate User access token using facebook login auth flow."""

import threading
import webbrowser
from fastapi import FastAPI, Request
from pydantic import BaseModel
import uvicorn
import httpx

from fbtools.official.models.response.fbauthflow import FbAuthResponse


# reusable and importable methods
async def get_access_token_from_callback(
    request: Request, client_id: str, client_secret: str, callback_function_name: str
) -> FbAuthResponse:
    """Will preprocess from the callback url of Facebook authentication flow.

    This will be use inside api route handler.

    Args:
        request: The request object.
        client_id: The client ID for the Facebook app.
        client_secret: The client secret for the Facebook app.
        callback_function_name: The name of the callback function used in your server.

    Returns:
        FbAuthResponse object with this data: access_token, message

    Raises:
        HttpxError: If the request fails.
        NoMatchFound: If the callback function is not found.

    """
    # to return
    to_return = FbAuthResponse(access_token="", message="")

    # Process successful callback
    code = request.query_params.get("code", "")

    # Handle potential errors
    if not code:
        to_return.message = "No code found in query params. Facebook might changed something or you used 'token' instead of 'code' as response_type."
        return to_return

    # Exchange code for access token
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://graph.facebook.com/v22.0/oauth/access_token",
            params={
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": str(request.url_for(callback_function_name)),
                "code": code,
            },
        )
        response.raise_for_status()
        response_data: dict[str, str] = response.json()
        access_token: str = response_data["access_token"]
        to_return.access_token = access_token

    return to_return


# ==============================================================================


class FacebookAuthFlow:
    """Facebook authentication flow class."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        localhost: str = "localhost",
        localhost_port: int = 3000,
        callback_route: str = "callback",
    ):
        """Initialize FacebookAuthFlow.

        Args:
            client_id: The client ID for the Facebook app.
            client_secret: The client secret for the Facebook app.
            localhost: Your custom localhost address.
            localhost_port: Your custom localhost port.
            callback_route: The custom callback route for the authentication flow of hosted server.

        """
        self.client_id: str = client_id
        self.client_secret: str = client_secret
        self.localhost: str = localhost
        self.localhost_port: int = localhost_port
        self.callback_route: str = callback_route
        self.access_token: str | None = None
        self.server: uvicorn.Server | None = None
        self.app: FastAPI = FastAPI()
        self._setup_routes()

    class Config(BaseModel):
        """Base model for configuration."""

        client_id: str
        client_secret: str

    def _setup_routes(self):

        async def handle_local_callback(request: Request):
            """Handle callback from Facebook authentication flow.

            This will be use inside api route handler. This is the
            basic usage of how to use `get_code_from_callback` and exchange code for
            token.

            Args:
                request: The request object.

            Returns:
                Dictionary of status message. Regarding if
                the process was successful or not.

            Notes:
                The process flow is:
                1. once this api route is called, you give the request, client id,
                    client secret and the function name of the api route that was
                    called to the `get_access_token_from_callback` function.
                    It will return a dictionary with the access token and the message.
                2. if the access_token is empty, it means something went wrong and check the
                    message. Otherwise, you need to catch common errors like HttpxError and
                    NoMatchFound (if the function name that used by your callback route is not found)

            """
            # get code from callback
            response_data = await get_access_token_from_callback(
                request=request,
                client_id=self.client_id,
                client_secret=self.client_secret,
                callback_function_name="handle_local_callback",
            )

            access_token = response_data.access_token

            if not access_token:
                self._shutdown()
                return {
                    "type": "error",
                    "message": "Failed to generate access token",
                }

            self.access_token = access_token
            self._shutdown()

            return {"message": "Success! You may close this window now."}

        self.app.add_api_route(
            "/" + self.callback_route, handle_local_callback, methods=["GET"]
        )

    def _shutdown(self):
        """Gracefully shutdown the server."""
        if self.server:
            self.server.should_exit = True

    def _run_server(self):
        """Run the FastAPI server with uvicorn."""
        config = uvicorn.Config(
            self.app, host=self.localhost, port=self.localhost_port, log_level="warning"
        )
        self.server = uvicorn.Server(config)
        self.server.run()

    def generate_auth_url(
        self,
        with_domain: str | None = None,
        scopes: str = "pages_manage_posts,pages_read_engagement",
    ) -> str:
        """Generate and return the OAuth URL.

        Args:
            with_domain: The domain to use for the OAuth URL.
            scopes: The scopes to request for the OAuth URL.

        Returns:
            The OAuth URL.

        """
        redirect_url = (
            f"https://{with_domain}/{self.callback_route}"
            if with_domain
            else f"http://{self.localhost}:{self.localhost_port}/{self.callback_route}"
        )
        return (
            "https://www.facebook.com/v22.0/dialog/oauth?"
            f"client_id={self.client_id}&"
            f"redirect_uri={redirect_url}&"
            f"scope={scopes}&"
            "response_type=code"
        )

    def get_token(self, scopes: str = "pages_manage_posts,pages_read_engagement"):
        """Start the authentication flow and return the token.

        Args:
            scopes: The scopes to request for the OAuth URL.

        Returns:
            The access token.

        """
        # Start server in background thread
        server_thread = threading.Thread(target=self._run_server, daemon=True)
        server_thread.start()

        # Generate and open OAuth URL
        auth_url = self.generate_auth_url(scopes=scopes)
        print("Opening url:", auth_url)
        webbrowser.open(auth_url)

        # Wait for completion (with timeout)
        server_thread.join(timeout=120)

        if not self.access_token:
            raise RuntimeError("Failed to retrieve access token")

        return self.access_token
