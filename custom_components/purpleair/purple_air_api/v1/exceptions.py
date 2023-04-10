"""Exceptions for the v1 PurpleAir API."""

from ..exceptions import PurpleAirApiError


class PurpleAirApiConfigError(PurpleAirApiError):
    """Raised when the config data is invalid.

    Attributes:
      extra   -- Extra info about the error
      param   -- The parameter that failed validation
      message -- An explanation of the error.
    """

    def __init__(self, param: str, extra: str | None = None) -> None:
        """Create an instance of the PurpleAirApiConfigError."""

        super().__init__(f"Invalid configuration parameter: {param} (extra: {extra})")
        self.param = param
        self.extra = extra


class PurpleAirServerApiError(PurpleAirApiError):
    """Raised when the API returns an error status code.

    Attributes:
      status
        The HTTP status code returned by the server. Refer to the HTTP standard to
        decipher how to read status codes and severity (ie: 4xx is a client (our) error,
        5xx is a server (their) error, but 503 may be transient, etc)
      reason
        The reason phrase given by the server, if one is available.
    """

    def __init__(self, status: int, reason: str) -> None:
        """Create a new PurpleAirServerApiError instance."""
        super().__init__(f"PurpleAir API returned HTTP {status} {reason}")
        self.status = status
        self.reason = reason


class PurpleAirApiDataError(PurpleAirApiError):
    """Raised when the API returns an error status code we can decipher a bit more.

    Attributes:
      status:
        The HTTP status code returned by the server.
      reason:
        The reason phrase given by the server, if one is available.
      description:
        The error description given for the error, if available.
      error:
        The attribute(s) the error may apply to, if available.
    """

    def __init__(self, status: int, reason: str, description: str, error: str) -> None:
        """Create a new PurpleAirApiDataError instance."""
        super().__init__(
            f"PurpleAir API returned HTTP {status} {reason}: {description} ({error})"
        )
        self.status = status
        self.reason = reason
        self.description = description
        self.error = error
