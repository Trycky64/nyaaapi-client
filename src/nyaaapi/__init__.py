"""Python package for the unofficial Nyaa API."""

from .client import AsyncNyaaAPI, NyaaAPI
from .constants import SortOrder
from .exceptions import (
    NyaaAPIError,
    NyaaAPIHTTPError,
    NyaaAPINotFoundError,
    NyaaAPIRateLimitError,
    NyaaAPIResponseError,
    NyaaAPITimeoutError,
)
from .models import HomeInfo, SearchResults, Torrent, TorrentComment, TorrentDetails

__version__ = "0.1.0"

__all__ = [
    "AsyncNyaaAPI",
    "HomeInfo",
    "NyaaAPI",
    "NyaaAPIError",
    "NyaaAPIHTTPError",
    "NyaaAPINotFoundError",
    "NyaaAPIRateLimitError",
    "NyaaAPIResponseError",
    "NyaaAPITimeoutError",
    "SearchResults",
    "SortOrder",
    "Torrent",
    "TorrentComment",
    "TorrentDetails",
    "__version__",
]
