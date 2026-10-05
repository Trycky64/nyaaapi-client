# nyaaapi-client

`nyaaapi-client` is a typed Python client for the **unofficial** [Nyaa-API](https://nyaaapi.onrender.com/docs). It supports the API's Nyaa and Sukebei search, uploader search, torrent detail, and home endpoints in synchronous and asynchronous clients.

The remote service and its response formats can change without notice. This package follows the currently observed API; review [the endpoint analysis](docs/api-analysis.md) when updating it.

## Requirements and installation

- Python 3.11 or newer
- Runtime dependency: `httpx`

Install the package:

```console
python -m pip install .
```

For development, install the test and quality tools too:

```console
python -m pip install -e ".[dev]"
```

## Synchronous use

### Search

`query` is sent to the API as `q`. Optional filters are sent only when supplied.

```python
from nyaaapi import NyaaAPI, SortOrder

with NyaaAPI() as api:
    results = api.search(
        query="Mushoku Tensei",
        sort="seeders",
        order=SortOrder.DESC,
        page=1,
    )
    for torrent in results:
        print(torrent.title, torrent.seeders)
```

Choose `source="sukebei"` to query Sukebei. `category`, `sub_category`, `sort`, and `order` are passed to the remote API as strings. OpenAPI documents `asc` and `desc` for order but provides no complete lists of category, sub-category, or sort values. The package therefore does not restrict those filters to locally invented choices. `SortOrder.ASC` and `SortOrder.DESC` are provided for the documented order values; plain strings work too.

### Search an uploader

```python
with NyaaAPI() as api:
    results = api.user("Tsundere-Raws", query="Mushoku Tensei")
    for torrent in results:
        print(torrent.title)
```

### Fetch a torrent by ID

```python
with NyaaAPI() as api:
    details = api.get(1234567)
    print(details.data.title, details.data.uploader)
```

### Iterate through pages

`iter_search()` and `iter_user()` yield torrents in page order, remove duplicate torrent links, and stop on an empty page or a page with no new links. Set `max_pages` to limit requests.

```python
with NyaaAPI() as api:
    for torrent in api.iter_search("Mushoku Tensei", max_pages=10):
        print(torrent.title)
```

## Asynchronous use

`AsyncNyaaAPI` provides the same endpoint methods and page iterators:

```python
import asyncio

from nyaaapi import AsyncNyaaAPI


async def main() -> None:
    async with AsyncNyaaAPI() as api:
        results = await api.search("Mushoku Tensei")
        print(len(results))
        async for torrent in api.iter_search("Mushoku Tensei", max_pages=3):
            print(torrent.title)


asyncio.run(main())
```

## Exceptions

All client exceptions derive from `NyaaAPIError`:

- `NyaaAPIHTTPError`: other HTTP errors or transport failures.
- `NyaaAPINotFoundError`: HTTP 404.
- `NyaaAPIRateLimitError`: HTTP 429.
- `NyaaAPITimeoutError`: an `httpx` timeout.
- `NyaaAPIResponseError`: invalid JSON or a non-object JSON response.

HTTP and response exceptions expose `status_code`, `endpoint`, and `server_message` where available. Network calls are reused through an `httpx.Client` or `httpx.AsyncClient`, and both clients support context managers for reliable cleanup.

## Tests and optional live checks

The default unit suite uses mocked transports and captured API fixtures; it does not depend on the live service. Run quality checks with:

```console
ruff check .
mypy src
pytest -q
python -m build
```

An optional live integration check is skipped by default. Enable it with `NYAAAPI_RUN_INTEGRATION=1` when running pytest.
