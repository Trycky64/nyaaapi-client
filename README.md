# nyaaapi-client

A typed Python 3.11+ client for the unofficial [Nyaa-API](https://nyaaapi.onrender.com/docs). Initial implementation covers the live API's search, uploader, item lookup, and home endpoints, in synchronous and asynchronous forms.

Install for development with `python -m pip install -e ".[dev]"`. The remote API is unofficial and can change; see [the endpoint analysis](docs/api-analysis.md).

```python
from nyaaapi import NyaaAPI

with NyaaAPI() as api:
    page = api.search(query="Mushoku Tensei", page=1)
    for torrent in page:
        print(torrent.title)
```
