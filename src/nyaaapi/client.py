"""Synchronous client for Nyaa-API."""

from __future__ import annotations

from typing import Any, Literal
from urllib.parse import quote

import httpx

from .constants import DEFAULT_BASE_URL, DEFAULT_TIMEOUT
from .exceptions import NyaaAPIResponseError
from .models import HomeInfo, SearchResults, TorrentDetails

Source = Literal["nyaa", "sukebei"]


def _params(query: str | None, category: str | None, sub_category: str | None,
            sort: str | None, order: str | None, page: int | None) -> dict[str, Any]:
    values = {"q": query, "category": category, "sub_category": sub_category,
              "sort": sort, "order": order, "page": page}
    return {key: value for key, value in values.items() if value is not None}


def _response_json(response: httpx.Response) -> dict[str, Any]:
    response.raise_for_status()
    try:
        data = response.json()
    except ValueError as exc:
        raise NyaaAPIResponseError("Nyaa-API returned invalid JSON") from exc
    if not isinstance(data, dict):
        raise NyaaAPIResponseError("Nyaa-API returned a non-object JSON response")
    return data


class NyaaAPI:
    """Reusable synchronous client for Nyaa and Sukebei endpoints."""

    def __init__(self, base_url: str = DEFAULT_BASE_URL, timeout: float = DEFAULT_TIMEOUT,
                 *, transport: httpx.BaseTransport | None = None) -> None:
        self._client = httpx.Client(base_url=base_url.rstrip("/"), timeout=timeout,
                                    transport=transport)

    def close(self) -> None:
        """Close the underlying HTTP connection pool."""
        self._client.close()

    def __enter__(self) -> NyaaAPI:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        return _response_json(self._client.get(path, params=params))

    def home(self) -> HomeInfo:
        """Return service metadata from `GET /`."""
        return HomeInfo.from_dict(self._get("/"))

    def search(self, query: str | None = None, *, category: str | None = None,
               sub_category: str | None = None, sort: str | None = None,
               order: str | None = None, page: int | None = 1,
               source: Source = "nyaa") -> SearchResults:
        """Search the selected source, mapping `query` to API parameter `q`."""
        params = _params(query, category, sub_category, sort, order, page)
        return SearchResults.from_dict(self._get(f"/{source}", params))

    def user(self, user_name: str, query: str | None = None, *, category: str | None = None,
             sub_category: str | None = None, sort: str | None = None,
             order: str | None = None, page: int | None = 1,
             source: Source = "nyaa") -> SearchResults:
        """Search uploads by username on the selected source."""
        path = f"/{source}/user/{quote(user_name, safe='')}"
        params = _params(query, category, sub_category, sort, order, page)
        return SearchResults.from_dict(self._get(path, params))

    def get(self, torrent_id: int, *, source: Source = "nyaa") -> TorrentDetails:
        """Fetch a torrent detail object by numeric ID."""
        return TorrentDetails.from_dict(self._get(f"/{source}/id/{torrent_id}"))
