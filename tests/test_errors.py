import asyncio

import httpx
import pytest

from nyaaapi import (
    AsyncNyaaAPI,
    NyaaAPI,
    NyaaAPIHTTPError,
    NyaaAPINotFoundError,
    NyaaAPIRateLimitError,
    NyaaAPIResponseError,
    NyaaAPITimeoutError,
)


@pytest.mark.parametrize(
    ("status", "expected"),
    [(404, NyaaAPINotFoundError), (429, NyaaAPIRateLimitError), (500, NyaaAPIHTTPError)],
)
def test_http_status_errors_include_server_context(
    status: int, expected: type[NyaaAPIHTTPError]
) -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(status, json={"detail": "service says no"})
    )
    with NyaaAPI(transport=transport) as api:
        with pytest.raises(expected) as caught:
            api.get(42)
    error = caught.value
    assert error.status_code == status
    assert error.endpoint == "/nyaa/id/42"
    assert error.server_message == "service says no"
    assert "service says no" in str(error)


def test_timeout_maps_to_client_timeout_error() -> None:
    def timeout(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("read timed out", request=request)

    with NyaaAPI(transport=httpx.MockTransport(timeout)) as api:
        with pytest.raises(NyaaAPITimeoutError) as caught:
            api.home()
    assert caught.value.endpoint == "/"
    assert "read timed out" in str(caught.value)


def test_transport_failure_maps_to_http_error() -> None:
    def fail(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection failed", request=request)

    with NyaaAPI(transport=httpx.MockTransport(fail)) as api:
        with pytest.raises(NyaaAPIHTTPError) as caught:
            api.home()
    assert caught.value.status_code is None
    assert caught.value.endpoint == "/"


@pytest.mark.parametrize(
    ("content", "message"),
    [(b"not-json", "invalid JSON"), (b"[]", "non-object JSON")],
)
def test_invalid_json_and_shape_include_context(content: bytes, message: str) -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200, content=content, headers={"content-type": "application/json"}
        )
    )
    with NyaaAPI(transport=transport) as api:
        with pytest.raises(NyaaAPIResponseError, match=message) as caught:
            api.home()
    assert caught.value.status_code == 200
    assert caught.value.endpoint == "/"


def test_async_errors_are_translated() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/":
            raise httpx.ConnectTimeout("connect timed out", request=request)
        return httpx.Response(404, json={"detail": "gone"})

    async def run() -> None:
        async with AsyncNyaaAPI(transport=httpx.MockTransport(handler)) as api:
            with pytest.raises(NyaaAPITimeoutError):
                await api.home()
            with pytest.raises(NyaaAPINotFoundError) as caught:
                await api.get(9)
        assert caught.value.status_code == 404
        assert caught.value.endpoint == "/nyaa/id/9"

    asyncio.run(run())
