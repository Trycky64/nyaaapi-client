import json
from pathlib import Path
from typing import Any

import httpx

from nyaaapi import NyaaAPI


def first_row() -> dict[str, Any]:
    return json.loads((Path(__file__).parent / "fixtures" / "search.json").read_text(encoding="utf-8"))["data"][0]


def test_pagination_deduplicates_and_stops_on_empty_page() -> None:
    row = first_row()
    calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        page = int(request.url.params["page"])
        calls.append(page)
        payload = {"count": 1, "data": [row]} if page < 3 else {"count": 0, "data": []}
        return httpx.Response(200, json=payload)

    with NyaaAPI(transport=httpx.MockTransport(handler)) as api:
        results = list(api.iter_search("title"))
    assert len(results) == 1
    assert calls == [1, 2, 3]


def test_pagination_honors_max_pages_and_uploader_route() -> None:
    row = first_row()
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(200, json={"count": 1, "data": [row]})

    with NyaaAPI(transport=httpx.MockTransport(handler)) as api:
        list(api.iter_user("Uploader", max_pages=2))
    assert len(calls) == 2
    assert [request.url.params["page"] for request in calls] == ["1", "2"]
    assert all(request.url.path == "/nyaa/user/Uploader" for request in calls)
