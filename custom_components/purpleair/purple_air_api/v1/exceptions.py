"""Exceptions for the v1 PurpleAir API."""

from ..exceptions import PurpleAirApiError


class PurpleAirApiConfigError(PurpleAirApiError):
    """Raised when the config data is invalid.

    Attributes:
      extra   -- Extra info about the error
      param   -- The parameter that failed validation
      message -- An explanation of the error.
    """

    def __init__(self, param: str, extra: str = None):
        super().__init__(f"Invalid configuration parameter: {param} (extra: {extra})")
        self.param = param
        self.extra = extra
