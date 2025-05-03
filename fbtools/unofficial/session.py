"""All HTTPS network and request.

Barebone https session for barebone requests.
"""

from httpx import AsyncClient

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
        # important public variables
        self._email: str = ""
        self._password: str = ""
        self._two_factor: str | None = None
        self._user_agent: UserAgent = user_agent or UserAgent()

        # checking variables
        self._need_relogin: bool = False

        # important private variables
        self._httpx_session: AsyncClient = self._generate_httpx_session()
        self._access_token: str | None = None

        # important variables for checking
        self._need_relogin_changes: list[str] = []

    async def login_as_browser(
        self,
        email: str,
        password: str,
        two_factor: str | None,
        custom_user_agent: str | None,
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

    @property
    def two_factor(self) -> str | None:
        """The two factor code of the user."""
        return self._two_factor

    @property
    def user_agent(self) -> UserAgent:
        """The user agent of the user."""
        return self._user_agent

    # ::::::::::::::::::::::::::::::::::::::::::::::::::
    # ::::::::::::::: PRIVATE METHODS ::::::::::::::::::
    # ::::::::::::::::::::::::::::::::::::::::::::::::::
    def _generate_httpx_session(self) -> AsyncClient:
        """Generate httpx async session.

        User agent must be fixed and not random, preferrably from the account
        holder themselves. The domain will be always on facebook to use other
        facebook related requests.
        """
        headers = {
            "Referer": "https://www.facebook.com",
            "User-Agent": self._user_agent.desktop_user_agent,
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
