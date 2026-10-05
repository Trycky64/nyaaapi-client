"""Typed exceptions raised while communicating with Nyaa-API."""


class NyaaAPIError(Exception):
    """Base error with optional HTTP status, endpoint, and server message."""

    def __init__(self, message: str, *, status_code: int | None = None,
                 endpoint: str | None = None, server_message: str | None = None) -> None:
        self.message = message
        self.status_code = status_code
        self.endpoint = endpoint
        self.server_message = server_message
        super().__init__(message)


class NyaaAPIHTTPError(NyaaAPIError):
    """An unsuccessful HTTP response or a failed HTTP transport request."""


class NyaaAPINotFoundError(NyaaAPIHTTPError):
    """The API returned HTTP 404 for a requested resource."""


class NyaaAPIRateLimitError(NyaaAPIHTTPError):
    """The API returned HTTP 429 indicating a rate limit."""


class NyaaAPIResponseError(NyaaAPIError):
    """The server response could not be decoded or did not match its expected shape."""


class NyaaAPITimeoutError(NyaaAPIError):
    """The request timed out before the service returned a response."""
