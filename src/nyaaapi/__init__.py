"""Python package for the unofficial Nyaa API."""

from .client import NyaaAPI
from .exceptions import NyaaAPIError, NyaaAPIResponseError
from .models import HomeInfo, SearchResults, Torrent, TorrentComment, TorrentDetails

__version__ = "0.1.0"

__all__ = ["HomeInfo", "NyaaAPI", "NyaaAPIError", "NyaaAPIResponseError", "SearchResults",
           "Torrent", "TorrentComment", "TorrentDetails", "__version__"]
