"""Synchronous client for Nyaa-API."""

from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable, Iterator
from typing import Any, Literal
from urllib.parse import quote

import httpx

from .constants import DEFAULT_BASE_URL, DEFAULT_TIMEOUT
from .exceptions import (
    NyaaAPIHTTPError,
    NyaaAPINotFoundError,
    NyaaAPIRateLimitError,
    NyaaAPIResponseError,
    NyaaAPITimeoutError,
)
from .models import HomeInfo, SearchResults, Torrent, TorrentDetails

Source = Literal["nyaa", "sukebei"]


def _params(query: str | None, category: str | None, sub_category: str | None,
            sort: str | None, order: str | None, page: int | None) -> dict[str, Any]:
    values = {"q": query, "category": category, "sub_category": sub_category,
              "sort": sort, "order": order, "page": page}
    return {key: value for key, value in values.items() if value is not None}


def _response_json(response: httpx.Response) -> dict[str, Any]:
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        error = _translate_http_error(exc)
        raise error from exc
    try:
        data = response.json()
    except ValueError as exc:
        raise NyaaAPIResponseError(
            "Nyaa-API returned invalid JSON", status_code=response.status_code,
            endpoint=response.request.url.path,
        ) from exc
    if not isinstance(data, dict):
        raise NyaaAPIResponseError(
            "Nyaa-API returned a non-object JSON response", status_code=response.status_code,
            endpoint=response.request.url.path,
        )
    return data


def _translate_http_error(error: httpx.HTTPError) -> Exception:
    response = error.response if isinstance(error, httpx.HTTPStatusError) else None
    request = response.request if response is not None else getattr(error, "request", None)
    endpoint = request.url.path if request is not None else None
    if isinstance(error, httpx.TimeoutException):
        return NyaaAPITimeoutError(str(error) or "Nyaa-API request timed out", endpoint=endpoint)
    if response is None:
        return NyaaAPIHTTPError(str(error), endpoint=endpoint)

    server_message: str | None = None
    try:
        body = response.json()
    except ValueError:
        body = None
    if isinstance(body, dict):
        detail = body.get("detail", body.get("message", body.get("error")))
        if detail is not None:
            server_message = str(detail)
    if server_message is None:
        text = response.text.strip()
        server_message = text or None

    message = f"Nyaa-API returned HTTP {response.status_code}"
    if server_message:
        message = f"{message}: {server_message}"
    error_type: type[NyaaAPIHTTPError]
    if response.status_code == 404:
        error_type = NyaaAPINotFoundError
    elif response.status_code == 429:
        error_type = NyaaAPIRateLimitError
    else:
        error_type = NyaaAPIHTTPError
    return error_type(message, status_code=response.status_code, endpoint=endpoint,
                      server_message=server_message)


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
        try:
            response = self._client.get(path, params=params)
        except httpx.TimeoutException as exc:
            raise _translate_http_error(exc) from exc
        except httpx.HTTPError as exc:
            raise _translate_http_error(exc) from exc
        return _response_json(response)

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

    def iter_search(self, query: str | None = None, *, page: int = 1,
                    max_pages: int | None = None, category: str | None = None,
                    sub_category: str | None = None, sort: str | None = None,
                    order: str | None = None, source: Source = "nyaa") -> Iterator[Torrent]:
        """Yield unique torrents across pages, stopping at an empty or repeated page."""
        return self._iterate(
            lambda current: self.search(
                query, page=current, category=category, sub_category=sub_category,
                sort=sort, order=order, source=source,
            ),
            page, max_pages,
        )

    def iter_user(self, user_name: str, query: str | None = None, *, page: int = 1,
                  max_pages: int | None = None, category: str | None = None,
                  sub_category: str | None = None, sort: str | None = None,
                  order: str | None = None, source: Source = "nyaa") -> Iterator[Torrent]:
        """Yield unique uploads for a user across pages."""
        return self._iterate(
            lambda current: self.user(
                user_name, query, page=current, category=category, sub_category=sub_category,
                sort=sort, order=order, source=source,
            ),
            page, max_pages,
        )

    @staticmethod
    def _iterate(fetch: Callable[[int], SearchResults], start_page: int,
                 max_pages: int | None) -> Iterator[Torrent]:
        current = start_page
        seen: set[str] = set()
        pages = 0
        while max_pages is None or pages < max_pages:
            results = fetch(current)
            pages += 1
            if not results.data:
                break
            fresh = 0
            for torrent in results:
                if torrent.link not in seen:
                    seen.add(torrent.link)
                    fresh += 1
                    yield torrent
            if fresh == 0:
                break
            current += 1


class AsyncNyaaAPI:
    """Reusable asynchronous client with the same routes and models as NyaaAPI."""

    def __init__(self, base_url: str = DEFAULT_BASE_URL, timeout: float = DEFAULT_TIMEOUT,
                 *, transport: httpx.AsyncBaseTransport | None = None) -> None:
        self._client = httpx.AsyncClient(base_url=base_url.rstrip("/"), timeout=timeout,
                                         transport=transport)

    async def close(self) -> None:
        """Close the underlying async connection pool."""
        await self._client.aclose()

    async def __aenter__(self) -> AsyncNyaaAPI:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        try:
            response = await self._client.get(path, params=params)
        except httpx.TimeoutException as exc:
            raise _translate_http_error(exc) from exc
        except httpx.HTTPError as exc:
            raise _translate_http_error(exc) from exc
        return _response_json(response)

    async def home(self) -> HomeInfo:
        """Return service metadata from `GET /`."""
        return HomeInfo.from_dict(await self._get("/"))

    async def search(self, query: str | None = None, *, category: str | None = None,
                     sub_category: str | None = None, sort: str | None = None,
                     order: str | None = None, page: int | None = 1,
                     source: Source = "nyaa") -> SearchResults:
        """Asynchronously search the selected source."""
        params = _params(query, category, sub_category, sort, order, page)
        return SearchResults.from_dict(await self._get(f"/{source}", params))

    async def user(self, user_name: str, query: str | None = None, *, category: str | None = None,
                   sub_category: str | None = None, sort: str | None = None,
                   order: str | None = None, page: int | None = 1,
                   source: Source = "nyaa") -> SearchResults:
        """Asynchronously search uploads by username."""
        path = f"/{source}/user/{quote(user_name, safe='')}"
        params = _params(query, category, sub_category, sort, order, page)
        return SearchResults.from_dict(await self._get(path, params))

    async def get(self, torrent_id: int, *, source: Source = "nyaa") -> TorrentDetails:
        """Asynchronously fetch a torrent detail object by numeric ID."""
        return TorrentDetails.from_dict(await self._get(f"/{source}/id/{torrent_id}"))

    async def iter_search(self, query: str | None = None, *, page: int = 1,
                          max_pages: int | None = None, category: str | None = None,
                          sub_category: str | None = None, sort: str | None = None,
                          order: str | None = None,
                          source: Source = "nyaa") -> AsyncIterator[Torrent]:
        """Yield unique search results across pages."""
        async for torrent in self._iterate(
            lambda current: self.search(
                query, page=current, category=category, sub_category=sub_category,
                sort=sort, order=order, source=source,
            ),
            page, max_pages,
        ):
            yield torrent

    async def iter_user(self, user_name: str, query: str | None = None, *, page: int = 1,
                        max_pages: int | None = None, category: str | None = None,
                        sub_category: str | None = None, sort: str | None = None,
                        order: str | None = None,
                        source: Source = "nyaa") -> AsyncIterator[Torrent]:
        """Yield unique uploads by a user across pages."""
        async for torrent in self._iterate(
            lambda current: self.user(
                user_name, query, page=current, category=category, sub_category=sub_category,
                sort=sort, order=order, source=source,
            ),
            page, max_pages,
        ):
            yield torrent

    @staticmethod
    async def _iterate(fetch: Callable[[int], Awaitable[SearchResults]], start_page: int,
                       max_pages: int | None) -> AsyncIterator[Torrent]:
        current = start_page
        seen: set[str] = set()
        pages = 0
        while max_pages is None or pages < max_pages:
            results: SearchResults = await fetch(current)
            pages += 1
            if not results.data:
                break
            fresh = 0
            for torrent in results:
                if torrent.link not in seen:
                    seen.add(torrent.link)
                    fresh += 1
                    yield torrent
            if fresh == 0:
                break
            current += 1
