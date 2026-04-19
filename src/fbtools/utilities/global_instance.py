"""Global static classes reusable throughout runtime."""

from asyncio import Future
from cachetools import TTLCache


class Cache:
    """Cache object."""

    _cache: TTLCache[str, Future[str]] = TTLCache(maxsize=1024, ttl=60 * 60 * 24)

    @classmethod
    def set_cache(cls, maxsize: int, ttl: int):
        """Set cache."""
        cls._cache = TTLCache(maxsize=maxsize, ttl=ttl)

    @classmethod
    def get_cache(cls) -> TTLCache[str, Future[str]]:
        """Get cache."""
        return cls._cache


class GraphApiVersion:
    """GraphApiVersion object.

    Import this object if you need to change
    the global version of the Graph API.
    """

    # Default version stored at the class level
    # This version is used throughout the library
    # means this is the current working and stable
    # that works with the library.
    _version: str = "v22.0"

    @classmethod
    def get_version(cls):
        """Get version of the Graph API."""
        return cls._version

    @classmethod
    def set_version(cls, value: str):
        """Set version of the Graph API."""
        cls._version = value
