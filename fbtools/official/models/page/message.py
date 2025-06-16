"""Message object.

This object will have full control of how you
handle a message.

Send a message and send a templated message.
"""

from typing import Literal
from fbtools.official.utilities.common import create_url_format

from httpx import AsyncClient


class FacebookMessage:
    """FacebookMessage object."""

    def __init__(
        self,
        sender: str,
        recipient: str,
        timestamp: int,
        message_id: str,
        session: AsyncClient,
        access_token: str,
        user_id: str | Literal["me"] = "me",
    ) -> None:
        """Initialize FacebookMessage.

        Args:
            sender: The sender id
            recipient: The recipient id
            timestamp: The timestamp of the message
            message_id: The message id
            session: The httpx async session object
            access_token: The page access token
            user_id: The user id or "me". The "me" is used on dev mode.

        """
        # important variables
        self._sender: str = sender
        self._recipient: str = recipient
        self._timestamp: int = timestamp

        # important inner variables
        self._user_id: str = user_id
        self._session: AsyncClient = session
        self._response_type: Literal["RESPONSE", "UPDATES", "TAGGED MESSAGE"] = (
            "RESPONSE"
        )
        self._headers: dict[str, str] = {"Content-Type": "application/json"}
        self._access_token: str = access_token

    # PUBlIC METHODS
    # ----------------------------------------
    async def send_text(self, text: str) -> "FacebookMessage":
        """Send a normal text."""
        data: dict[str, object] = {"message": {"text": text}}
        await self._send_api(data)
        raise NotImplementedError

    # OBJECT CONTROL
    # ----------------------------------------
    def set_response_type(
        self, response_type: Literal["RESPONSE", "UPDATES", "TAGGED MESSAGE"]
    ):
        """Set the response type.

        Default is "RESPONSE".
        """
        self._response_type = response_type

    # PRIVATE METHODS
    # ----------------------------------------
    async def _send_api(self, data: dict[str, object]) -> "FacebookMessage":
        """Centralize of sending data to the API."""
        # preprocess data
        # --------------------
        # automatically use sender id as a recipient for sending messages back
        data.update({"recipient": {"id": self._sender}})
        # set response type
        data.update({"messaging_type": self._response_type})
        # set params
        params = {"access_token": self._access_token}

        url = create_url_format(f"{self._user_id}/messages")
        print(url)

        response = await self._session.post(
            url=url, json=data, params=params, headers=self._headers
        )
        print(response.json())
        raise NotImplementedError
