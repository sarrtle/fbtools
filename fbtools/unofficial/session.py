"""All HTTPS network and request.

Barebone https session for barebone requests.
"""

from json import JSONDecodeError
from random import random
from re import search
from typing import cast
from httpx import URL, AsyncClient, Response

from bs4 import BeautifulSoup, NavigableString, SoupStrainer, Tag

from fbtools.unofficial.exceptions.common import NeedRelogIn
from fbtools.unofficial.utilities.user_agent import UserAgent


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
        self._fb_dtsg: str = ""
        self._cookies: dict[str, str] = {}
        self._user_id: str = ""
        self._client_id: str = ""

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
    ) -> None:
        """Safely login that simulates browser with https request.

        This feature may not work in the future as Facebook seems improving their security
        measures. This one is slow but keeps your account from locking.


        Args:
            email: The email of the user.
            password: The password of the user.
            two_factor: The two factor code of the user.
            custom_user_agent: The custom user agent of the user.

        Raises:
            RuntimeError: if something went wrong during login.

        """
        self._email = email
        self._password = password
        self._two_factor = two_factor

        # create a new separate session for login
        # will register this login session later
        # to be use by the whole session
        session = self._generate_httpx_session()

        # change user agent to mobile for login only
        session.headers["User-Agent"] = self._user_agent.mobile_user_agent

        # first step
        # getting login form
        response = await session.get(self._mobile_url)

        soup = BeautifulSoup(
            response.content, "html.parser", parse_only=SoupStrainer("input")
        )

        login_payload: dict[str, str] = {}

        for element in soup:
            # recasting this to Tag element because beautifulsoup
            # is so lazy handling types which results to Any
            element = cast(Tag, element)

            if not element.has_attr("name") and not element.has_attr("value"):
                continue

            name = element.attrs.get("name", "")
            value = element.attrs.get("value", "")

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
        login_payload["_fb_noscript"] = "true"

        response = await session.post(
            self._mobile_url + "/login.php?login_attempt=1", data=login_payload
        )

        if "checkpoint" in str(response.url):
            print("Starting 2FA flow...")
            response = await self._handle_two_factor(session=session, response=response)

        # generate persistent session object that will be used
        # throughout the whole Session object and check if login
        # was truly successful
        await self._generate_session_object(session=session)

    async def login_as_cookies(self, cookies: dict[str, str]) -> None:
        """Login using cookies.

        Args:
            cookies: The cookies dictionary data of the user from previous session.

        Raises:
            RuntimeError: if something went wrong during login.

        """
        session = self._generate_httpx_session()
        session.cookies.update(cookies)
        await self._generate_session_object(session=session)
        print("Login using cookies completed.")

    def get_cookies(self) -> dict[str, str]:
        """Get cookies as dictionary."""
        cookies = self._session.cookies

        return dict(cookies)

    async def is_logged_in(self) -> bool:
        """Check if session is already logged in."""
        response = await self._session.get(url=self._mobile_url + "/login")

        return "home" in str(response.url)

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
            "User-Agent": self._user_agent.desktop_user_agent,
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "same-origin",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "Accept-Language": "en-Us,en;q=0.5",
            "Connection": "keep-alive",
        }

        return AsyncClient(headers=headers, follow_redirects=True, timeout=30)

    def _is_need_relogin(self) -> bool:
        """Check if need relogin.

        Raises:
            NeedRelogIn: If need relogin.

        """
        if self._need_relogin:
            self._need_relogin = False

        raise NeedRelogIn(what_variable=", ".join(self._need_relogin_changes))

    async def _handle_two_factor(
        self, session: AsyncClient, response: Response
    ) -> Response:
        """Handle two factor login.

        Raises:
            RuntimeError: If two factor code is not set.

        """
        if not self.two_factor:
            raise RuntimeError("Two factor code is not set")

        def check_if_complete(response: Response) -> bool:
            """We got some skip part where it initially finalize the login.

            And sometimes the URL is redirected to fb:// which is not
            an https:// so we need to handle the redirection on the current
            working user agent.

            Args:
                response: The current response object.

            """
            if response.status_code == 302 and "home" in response.headers["Location"]:
                # apply the URL location of the homepage that was taken from the headers.
                response.request.url = URL(response.headers["Location"])
                return True
            return False

        # need new httpx session for checking code from another api
        # we already assume that this api will work, it may fail if there
        # are some changes on API, but after all those years it seems normal.
        # but better watch out.
        two_factor_response = await AsyncClient().get(
            url="https://2fa.live/tok/{}".format("".join(self.two_factor.split(" ")))
        )
        try:
            two_factor_data = cast(dict[str, str], two_factor_response.json())
        except JSONDecodeError as exc:
            raise RuntimeError(
                f"Two factor code is not valid: {exc}\n{two_factor_response.text}"
            )

        if "token" not in two_factor_data:
            raise RuntimeError(
                "token object not found on json data, possible some changes or error, please check the API."
            )

        two_factor_code = two_factor_data["token"]

        # parse checkpoint html response from facebook
        soup = BeautifulSoup(
            response.content, "html.parser", parse_only=SoupStrainer("input")
        )

        # find important variables for form purposes
        fb_dtsg = ""
        nh_ = ""

        # find fb_dtsg
        fbdtsg_element = soup.find("input", attrs={"name": "fb_dtsg"})
        if fbdtsg_element is None or isinstance(fbdtsg_element, NavigableString):
            raise RuntimeError("Failed to find fb_dtsg")

        fb_dtsg = fbdtsg_element["value"]
        if not isinstance(fb_dtsg, str):
            raise RuntimeError(
                f"Something went wrong when getting `fb_dtsg` value, expecting a string, found a {type(fb_dtsg)}"
            )

        # find nh_
        nh_element = soup.find("input", attrs={"name": "nh"})
        if nh_element is None or isinstance(nh_element, NavigableString):
            raise RuntimeError("Failed to find nh_")

        nh = nh_element["value"]
        if not isinstance(nh, str):
            raise RuntimeError(
                f"Something went wrong when getting `nh` value, expecting a string, found a {type(nh_)}"
            )

        # construct two factor payload data
        two_factor_payload: dict[str, str] = {}
        two_factor_payload["approvals_code"] = two_factor_code
        two_factor_payload["fb_dtsg"] = fb_dtsg
        two_factor_payload["nh"] = nh
        two_factor_payload["submit[Submit Code]"] = "Submit Code"
        two_factor_payload["codes_submitted"] = "0"

        # submit code
        print("Submitting two factor code...")
        checkpoint_url = self._mobile_url + "/login/checkpoint/"
        response = await session.post(url=checkpoint_url, data=two_factor_payload)

        # save device state
        del two_factor_payload["approvals_code"]
        del two_factor_payload["submit[Submit Code]"]
        del two_factor_payload["codes_submitted"]

        two_factor_payload["name_action_selected"] = "save_device"
        two_factor_payload["submit[Continue]"] = "Continue"

        # submit device
        # this time redirection is not allowed so we wont get the
        # fb:// url if everything went well
        print("Submitting device...")
        response = await session.post(
            url=checkpoint_url, data=two_factor_payload, follow_redirects=False
        )

        # check early return if everything is completed
        if check_if_complete(response=response):
            return response

        # Facebook checkup flow, click continue part
        print("Starting facebook checkup flow...")
        del two_factor_payload["name_action_selected"]
        response = await session.post(url=checkpoint_url, data=two_factor_payload)

        # clicking this was me
        print("Clicking this was me...")
        del two_factor_payload["submit[Continue]"]
        two_factor_payload["submit[This was me]"] = "This Was Me"
        response = await session.post(url=checkpoint_url, data=two_factor_payload)

        # saving device again
        # made sure that redirection is false so session will continue
        # to have the https:// url
        print("Saving device again...")
        del two_factor_payload["submit[This was me]"]
        two_factor_payload["name_action_selected"] = "save_device"
        two_factor_payload["submit[Continue]"] = "Continue"

        response = await session.post(
            url=checkpoint_url, data=two_factor_payload, follow_redirects=False
        )

        return response

    async def _generate_session_object(self, session: AsyncClient) -> None:
        """Finalize the session object and get required data.

        Some data don't need to change, only fb_dtsg is only needed
        to change per session.

        Args:
            session: The session object.

        Raises:
            RuntimeError: Failed to get fb_dtsg value.
            NotLoggedIn: User is not logged in or failed to login.

        """
        # apply session object to the global session
        self._session = session

        # return to desktop user agent for full features api
        self._session.headers["User-Agent"] = self._user_agent.desktop_user_agent

        # using this accept to enable html response
        self._session.headers["Accept"] = "text/html"

        # get fb_dtsg value
        response = await self._session.get(url=self._desktop_url + "/login")

        # delete the html accept on headers because it is not required
        # on API requests for later
        del self._session.headers["Accept"]

        if "home" not in str(response.url):
            raise Exception("NotLoggedIn")

        # use regex to find fb_dtsg value
        # fb_dtsg value can be found on script tag inside DTSGInitData>token
        pattern = r'\["DTSGInitData",\[\],\{"token":"([^"]+)"'
        match = search(pattern, response.text)
        if not match:
            raise Exception("NoFbDtsg")

        fb_dtsg: str = match.group(1)

        self._fb_dtsg = fb_dtsg

        # get cookies
        self._cookies = self.get_cookies()

        # apply required data
        self._user_id = self._cookies["c_user"]
        self._client_id = hex(int(random() * 2**31))[2:]

        # ensure all data are set
        if self._user_id == "":
            raise RuntimeError("Failed to get user id")

        if self._client_id == "":
            raise RuntimeError("Failed to get client id")
