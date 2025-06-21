"""Global instances reusable for fbtools official graph."""

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

    _version: str = "v22.0"  # Default version stored at the class level

    @classmethod
    def get_version(cls):
        """Get version of the Graph API."""
        return cls._version

    @classmethod
    def set_version(cls, value: str):
        """Set version of the Graph API."""
        cls._version = value
