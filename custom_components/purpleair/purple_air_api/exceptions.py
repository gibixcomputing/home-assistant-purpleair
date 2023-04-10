"""Contains errors that can be raised by the PurpleAirApi."""
from __future__ import annotations

from typing import Any


class PurpleAirApiError(Exception):
    """Raised when an error with the PurpleAir APi is encountered.

    Attributes:
        message -- An explanation of the error.
    """

    def __init__(self, message: str) -> None:
        """Create a new PurpleAirApiError."""
        super().__init__()
        self.message = message

    def __str__(self) -> str:
        """Return a string representation of this error."""
        return f"[{self.__class__.__name__}]: {self.message}"


class PurpleAirApiInvalidResponseError(PurpleAirApiError):
    """Raised when the data from PurpleAir cannot be parsed.

    Attributes:
      message -- An explanation of the error.
      data    -- Data returned from the API call that could not be recognized.
    """

    def __init__(self, message: str, data: Any) -> None:
        """Create a new PurpleAirApiInvalidResponseError."""

        super().__init__(message)
        self.data = data


class PurpleAirApiStatusError(PurpleAirApiError):
    """Raised when an error occurs when communicating with the PurpleAir API.

    Attributes:
        message -- Generic error message.
        url     -- The URL that caused the error.
        status  -- Status code returned from the server.
        text    -- Any data returned in the body of the error from the server.
    """

    def __init__(self, url: str, status: int, text: str) -> None:
        """Create a new PurpleAirApiStatusError."""

        super().__init__(
            "An error occurred while communicating with the PurpleAir API."
        )
        self.url = url
        self.status = status
        self.text = text


class PurpleAirApiUrlError(PurpleAirApiError):
    """Raised when an invalid PurpleAir URL is encountered.

    Attributes:
        message -- An explanation of the error.
        url     -- The URL that is considered invalid.
    """

    def __init__(self, message: str, url: str) -> None:
        """Create a new PurpleAirApiUrlError."""

        super().__init__(message)
        self.url = url
