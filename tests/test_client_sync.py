import json
from pathlib import Path
from typing import Any

import httpx
import pytest

from nyaaapi import NyaaAPI
from nyaaapi.exceptions import NyaaAPIResponseError


def load_fixture(name: str) -> dict[str, Any]:
    return json.loads((Path(__file__).parent / "fixtures" / f"{name}.json").read_text(encoding="utf-8"))


def test_search_sends_defined_params_only() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={"count": 0, "data": []})

    with NyaaAPI(transport=httpx.MockTransport(handler)) as api:
        result = api.search("Mushoku Tensei", category="1_2", page=2)
    assert len(result) == 0
    assert requests[0].url.path == "/nyaa"
    assert dict(requests[0].url.params) == {"q": "Mushoku Tensei", "category": "1_2", "page": "2"}


def test_user_and_id_routes_parse_fixture_data() -> None:
    payloads = [load_fixture("user"), load_fixture("detail")]
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=payloads[len(requests) - 1])

    with NyaaAPI(transport=httpx.MockTransport(handler)) as api:
        result = api.user("Tsundere-Raws")
        details = api.get(1234567)
    assert len(result) == 75
    assert details.data.infohash
    assert requests[0].url.path == "/nyaa/user/Tsundere-Raws"
    assert requests[1].url.path == "/nyaa/id/1234567"


def test_http_errors_propagate_and_invalid_json_is_reported() -> None:
    with NyaaAPI(transport=httpx.MockTransport(lambda request: httpx.Response(404))) as api:
        with pytest.raises(httpx.HTTPStatusError):
            api.home()
    with NyaaAPI(transport=httpx.MockTransport(lambda request: httpx.Response(200, text="nope"))) as api:
        with pytest.raises(NyaaAPIResponseError):
            api.home()
