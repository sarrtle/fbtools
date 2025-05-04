"""Utility functions and classes for fbtools unofficial."""

COMMON_DESKTOP_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0"
)
COMMON_MOBILE_USER_AGENT = "Dalvik/2.1.0 (Linux; U; Android 8.0.0; SM-G930F Build/R16NW) [FBAN/FB4A;FBAV/187.0.0.43.81;FBPN/com.facebook.katana;FBLC/en_US;FBBV/122388438;FBCR/Bouygues Telecom;FBMF/samsung;FBBD/samsung;FBDV/SM-G930F;FBSV/8.0.0;FBCA/armeabi-v7a:armeabi;FBDM/{density=3.0,width=1080,h"


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
        self.mobile_user_agent: str = desktop_user_agent or COMMON_MOBILE_USER_AGENT
