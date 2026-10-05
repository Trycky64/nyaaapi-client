"""Response parsing exceptions used by NyaaAPI clients."""


class NyaaAPIError(Exception):
    """Base exception raised by this client."""


class NyaaAPIResponseError(NyaaAPIError):
    """Raised when the service response is not valid JSON object data."""
