"""Will generate User access token using facebook login auth flow."""

import threading
import webbrowser
from fastapi import FastAPI, Request
from pydantic import BaseModel
import uvicorn
import httpx


class FacebookAuthFlow:
    """Facebook authentication flow class."""

    def __init__(self, client_id: str, client_secret: str):
        """Initialize FacebookAuthFlow.

        Args:
            client_id (str): The client ID for the Facebook app.
            client_secret (str): The client secret for the Facebook app.

        """
        self.client_id: str = client_id
        self.client_secret: str = client_secret
        self.access_token: str | None = None
        self.server: uvicorn.Server | None = None
        self.app: FastAPI = FastAPI()
        self._setup_routes()

    class Config(BaseModel):
        """Base model for configuration."""

        client_id: str
        client_secret: str

    def _setup_routes(self):
        async def handle_callback(request: Request):
            # Handle potential errors
            if "error" in request.query_params:
                error = request.query_params["error"]
                print(f"Auth error: {error}")
                await self._shutdown()
                return {"error": "Authentication failed"}

            # Process successful callback
            code = request.query_params.get("code")
            if not code:
                await self._shutdown()
                return {"error": "Missing authorization code"}

            await self._exchange_code_for_token(code, request)
            await self._shutdown()
            return {"message": "Authentication successful! You can close this tab."}

        self.app.add_api_route("/callback", handle_callback, methods=["GET"])

    async def _exchange_code_for_token(self, code: str, request: Request):
        """Exchange OAuth code for access token.

        Args:
            code: The OAuth code received from the callback URL.
            request: The FastAPI request object.

        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://graph.facebook.com/v22.0/oauth/access_token",
                    params={
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "redirect_uri": str(request.url_for("handle_callback")),
                        "code": code,
                    },
                )
                response.raise_for_status()
                self.access_token = response.json()["access_token"]
        except Exception as e:
            print(f"Token exchange failed: {e}")
            self.access_token = None

    async def _shutdown(self):
        """Gracefully shutdown the server."""
        if self.server:
            self.server.should_exit = True

    def _run_server(self):
        """Run the FastAPI server with uvicorn."""
        config = uvicorn.Config(
            self.app, host="0.0.0.0", port=5000, log_level="warning"
        )
        self.server = uvicorn.Server(config)
        self.server.run()

    def get_token(self, scopes: str = "pages_manage_posts,pages_read_engagement"):
        """Start the authentication flow and return the token."""
        # Start server in background thread
        server_thread = threading.Thread(target=self._run_server, daemon=True)
        server_thread.start()

        # Generate and open OAuth URL
        auth_url = (
            "https://www.facebook.com/v22.0/dialog/oauth?"
            f"client_id={self.client_id}&"
            f"redirect_uri=http://localhost:5000/callback&"
            f"scope={scopes}&"
            "response_type=code"
        )
        print("Opening url:", auth_url)
        webbrowser.open(auth_url)

        # Wait for completion (with timeout)
        server_thread.join(timeout=120)

        if not self.access_token:
            raise RuntimeError("Failed to retrieve access token")

        return self.access_token
