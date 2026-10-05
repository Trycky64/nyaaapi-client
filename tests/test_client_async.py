import asyncio
import json
from pathlib import Path
from typing import Any

import httpx

from nyaaapi import AsyncNyaaAPI


def load_fixture(name: str) -> dict[str, Any]:
    path = Path(__file__).parent / "fixtures" / f"{name}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_async_routes_and_pagination() -> None:
    row = load_fixture("search")["data"][0]
    detail = load_fixture("detail")
    requests: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path.endswith("/id/1234567"):
            return httpx.Response(200, json=detail)
        if request.url.path == "/nyaa/user/Someone":
            return httpx.Response(200, json={"count": 1, "data": [row]})
        page = int(request.url.params["page"])
        data = [row] if page == 1 else []
        return httpx.Response(200, json={"count": len(data), "data": data})

    async def run() -> None:
        async with AsyncNyaaAPI(transport=httpx.MockTransport(handler)) as api:
            search = await api.search("Mushoku Tensei")
            user = await api.user("Someone")
            torrent = await api.get(1234567)
            paged = [item async for item in api.iter_search("Mushoku Tensei")]
        assert len(search) == len(user) == len(paged) == 1
        assert torrent.data.uploader == "Judas"

    asyncio.run(run())
    assert any(request.url.path == "/nyaa/id/1234567" for request in requests)
    assert sum(request.url.path == "/nyaa" for request in requests) == 3
