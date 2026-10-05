"""Typed representations of fields observed in Nyaa-API responses."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime
from typing import Any


def _date(value: str | None) -> datetime | None:
    if value is None:
        return None
    return datetime.fromisoformat(value.replace(" UTC", "+00:00"))


@dataclass(frozen=True, slots=True)
class TorrentComment:
    """Comment attached to a torrent detail response."""

    user: str
    profile_url: str
    avatar: str
    comment_body: str
    time: datetime | None
    link: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TorrentComment:
        """Parse a comment object returned in a torrent detail."""
        return cls(data["user"], data["profileUrl"], data["avatar"], data["commentBody"],
                   _date(data.get("time")), data["link"])


@dataclass(frozen=True, slots=True)
class Torrent:
    """Torrent fields present in search and detail responses."""

    category: str
    title: str
    link: str
    torrent: str
    magnet: str
    size: str
    time: datetime | None
    seeders: int
    leechers: int
    downloads: int
    uploader: str | None = None
    information: str | None = None
    infohash: str | None = None
    comments: tuple[TorrentComment, ...] | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Torrent:
        """Parse the common torrent fields and optional detail-only fields."""
        comments = data.get("comments")
        return cls(
            category=data["category"], title=data["title"], link=data["link"],
            torrent=data["torrent"], magnet=data["magnet"], size=data["size"],
            time=_date(data.get("time")), seeders=data["seeders"], leechers=data["leechers"],
            downloads=data["downloads"], uploader=data.get("uploader"),
            information=data.get("information"), infohash=data.get("infohash"),
            comments=tuple(TorrentComment.from_dict(comment) for comment in comments)
            if comments is not None else None,
        )


@dataclass(frozen=True, slots=True)
class SearchResults:
    """Search envelope containing a count and current-page torrent rows."""

    count: int
    data: tuple[Torrent, ...]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SearchResults:
        """Parse a search response object."""
        return cls(data["count"], tuple(Torrent.from_dict(item) for item in data["data"]))

    def __iter__(self) -> Iterator[Torrent]:
        return iter(self.data)

    def __len__(self) -> int:
        return len(self.data)


@dataclass(frozen=True, slots=True)
class TorrentDetails:
    """Detail response envelope for an individual torrent."""

    data: Torrent

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TorrentDetails:
        """Parse a detail response object."""
        return cls(Torrent.from_dict(data["data"]))


@dataclass(frozen=True, slots=True)
class HomeInfo:
    """Fields observed at the API home endpoint."""

    app: str
    version: str
    ip: str
    uptime: float

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> HomeInfo:
        """Parse the home response object."""
        return cls(data["app"], data["version"], data["ip"], data["uptime"])
