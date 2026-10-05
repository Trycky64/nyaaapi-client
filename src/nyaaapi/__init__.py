"""Python package for the unofficial Nyaa API."""

from .models import HomeInfo, SearchResults, Torrent, TorrentComment, TorrentDetails

__version__ = "0.1.0"

__all__ = ["HomeInfo", "SearchResults", "Torrent", "TorrentComment", "TorrentDetails", "__version__"]
