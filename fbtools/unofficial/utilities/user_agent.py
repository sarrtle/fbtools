"""Utility functions and classes for fbtools unofficial."""

COMMON_DESKTOP_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) facebook-nativefier-f52d2f/1.0.0 Chrome/53.0.2785.143 Electron/1.4.16 Safari/537.36"
COMMON_MOBILE_USER_AGENT = "SupportsFresco=1 modular=3 Dalvik/2.1.0 (Linux; U; Android 12; TECNO BF6 Build/SP1A.210812.001) [FBAN/EMA;FBBV/509523294;FBAV/370.0.0.16.116;FBDV/TECNO BF6;FBSV/12;FBCX/OkHttp3;FBDM/{density=2.0}]"


class UserAgent:
    """User agent for fbtools unofficial.

    Attributes:
        desktop_user_agent: The user agent for desktop.
        mobilefb_user_agent: The user agent for mobile.

    """

    def __init__(
        self,
        desktop_user_agent: str | None = None,
        mobilefb_user_agent: str | None = None,
    ) -> None:
        """Initialize UserAgent."""
        self.desktop_user_agent: str = desktop_user_agent or COMMON_DESKTOP_USER_AGENT
        self.mobile_user_agent: str = mobilefb_user_agent or COMMON_MOBILE_USER_AGENT
