"""All HTTPS network and request.

Barebone https session for barebone requests.
"""

from typing import cast
from httpx import AsyncClient, Response

from bs4 import BeautifulSoup, ResultSet, Tag

from fbtools.unofficial.exceptions.common import NeedRelogIn
from fbtools.unofficial.utility import UserAgent


class Session:
    """Manages all HTTPS request for the facebook session.

    This class handles HTTP requests like GET and POST, which are used for
    actions such as logging in, sending messages, reacting to posts, and
    commenting on posts.
    """

    def __init__(self, user_agent: UserAgent | None = None) -> None:
        """Initialize Session.

        Args:
            user_agent: The user agent for the session.

        """
        # attributes
        self._email: str = ""
        self._password: str = ""
        self._two_factor: str | None = None
        self._user_agent: UserAgent = user_agent or UserAgent()
        self._current_user_agent: str = self._user_agent.desktop_user_agent

        # checking variables
        self._need_relogin: bool = False
        self._need_relogin_changes: list[str] = []

        # private variables
        self._session: AsyncClient = self._generate_httpx_session()
        self._access_token: str | None = None

        self._mobile_url: str = "https://m.facebook.com"
        self._desktop_url: str = "https://www.facebook.com"

    async def login_as_browser(
        self,
        email: str,
        password: str,
        two_factor: str | None,
        custom_user_agent: UserAgent | None,
    ) -> None:
        """Safely login that simulates browser with https request.

        This feature may not work in the future as Facebook seems improving their security
        measures. This one is slow but keeps your account from locking.


        Args:
            email: The email of the user.
            password: The password of the user.
            two_factor: The two factor code of the user.
            custom_user_agent: The custom user agent of the user.

        """
        self._email = email
        self._password = password
        self._two_factor = two_factor

        if custom_user_agent:
            self._user_agent = custom_user_agent

        self._current_user_agent = self._user_agent.mobile_user_agent
        self._session = self._generate_httpx_session()

        # first step
        # getting login form
        response = await self._session.get(self._mobile_url)

        soup = BeautifulSoup(response.text, "html.parser")

        login_payload: dict[str, str] = {}

        for element in cast(ResultSet[Tag], soup.find_all("input")):
            name = cast(str, element.get("name"))
            value = cast(str, element.get("value"))

            if name and value:
                login_payload[name] = value

        # checking if the user agent is good
        if "jazoest" not in login_payload:
            raise Exception("TODO: BadUserAgent Exception")

        # second step, send login data
        login_payload["email"] = self._email
        login_payload["pass"] = self._password
        login_payload["login"] = "Log In"

        # removing this might say we are on browser
        login_payload["_fb_noscript"] = "false"

        import json

        print(json.dumps(login_payload, indent=4))

        response = await self._session.post(
            self._mobile_url + "/login.php?login_attempt=1", json=login_payload
        )

        print(response.status_code, response.url)

        self._debug_html(1, response)

    # :::::::::::::::::::::::::::::::::::::::::::::::::
    # ::::::::::::::: Properties ::::::::::::::::::::::
    # :::::::::::::::::::::::::::::::::::::::::::::::::

    # email
    @property
    def email(self) -> str:
        """The email of the user."""
        return self._email

    @email.setter
    def email(self, value: str) -> None:
        """Set the email of the user.

        Requires re login to refresh session that will
        use the new email

        Args:
            value: The email of the user.

        """
        self._email = value
        self._need_relogin_changes.append("email")

    # password
    @property
    def password(self) -> str:
        """The password of the user."""
        return self._password

    @password.setter
    def password(self, value: str) -> None:
        """Set the password of the user.

        Requires re login to refresh session that will
        use the new password

        Args:
            value: The password of the user.

        """
        self._password = value
        self._need_relogin_changes.append("password")

    @property
    def two_factor(self) -> str | None:
        """The two factor code of the user."""
        return self._two_factor

    @two_factor.setter
    def two_factor(self, value: str | None) -> None:
        """Set the two factor code of the user.

        Requires re login to refresh session that will
        use the new two factor code

        Args:
            value: The two factor code of the user.

        """
        self._two_factor = value
        self._need_relogin_changes.append("two_factor")

    @property
    def user_agent(self) -> UserAgent:
        """The user agent of the user."""
        return self._user_agent

    # ::::::::::::::::::::::::::::::::::::::::::::::::::
    # ::::::::::::::: PRIVATE METHODS ::::::::::::::::::
    # ::::::::::::::::::::::::::::::::::::::::::::::::::
    def _debug_html(self, id: int, response: Response) -> None:
        """Generate an html from response."""
        with open(f"debug_{id}.html", "w") as f:
            f.write(response.text)

    def _generate_httpx_session(self) -> AsyncClient:
        """Generate httpx async session.

        User agent must be fixed and not random, preferrably from the account
        holder themselves. The domain will be always on facebook to use other
        facebook related requests.
        """
        headers = {
            "Referer": "https://www.facebook.com",
            "User-Agent": self._current_user_agent,
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "same-origin",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
        }

        return AsyncClient(headers=headers, follow_redirects=True)

    def _is_need_relogin(self) -> bool:
        """Check if need relogin.

        Raises:
            NeedRelogIn: If need relogin.

        """
        if self._need_relogin:
            self._need_relogin = False

        raise NeedRelogIn(what_variable=", ".join(self._need_relogin_changes))
