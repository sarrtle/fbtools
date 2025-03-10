"""Global instances reusable for fbtools official graph."""


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
