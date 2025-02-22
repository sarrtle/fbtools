"""All exception objects for official APIs."""


class UserValidationError(Exception):
    """Raise if something went wrong during validation of login on user."""

    def __init__(self, message: str):
        """Initialize UserValidationError."""
        super().__init__(message)


class PageValidationError(Exception):
    """Raise if something went wrong during validation of login on page."""

    def __init__(self, message: str):
        """Initialize PageValidationError."""
        super().__init__(message)


class UnknownValidationError(Exception):
    """Raise if something went wrong during validation of login on page."""

    def __init__(self, message: str):
        """Initialize PageValidationError."""
        super().__init__(message)


class LoginError(Exception):
    """Raise if something went wrong during login."""

    def __init__(
        self,
        error_type: UserValidationError | PageValidationError | UnknownValidationError,
    ):
        """Initialize LoginError."""
        if isinstance(error_type, UserValidationError):
            message = "Error during login: Can't validate user token."
        elif isinstance(error_type, PageValidationError):
            message = "Error during login: Can't validate page token."
        else:
            message = "Error during login: Unknown error."
        super().__init__(message)
