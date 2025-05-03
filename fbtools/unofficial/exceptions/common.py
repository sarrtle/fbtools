"""Common exceptions for unofficial fbtools."""


class NeedRelogIn(Exception):
    """When needing relogin to refresh session."""

    def __init__(self, what_variable: str) -> None:
        """Inititialize NeedRelogIn."""
        message: str = (
            "Need relogin to refresh the session because you change: `%s`"
            % what_variable
        )
        super().__init__(message)
