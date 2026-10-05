# Nyaa-API analysis

Observed against the live Swagger document at `https://nyaaapi.onrender.com/docs` and its schema at `https://nyaaapi.onrender.com/openapi.json` on 2026-10-05. The exact schema snapshot is [openapi.json](openapi.json). GET requests were sent to every documented route; response samples are in `tests/fixtures/`.

## Endpoints

| Method and route | Parameters | Success response | Documented errors / observed errors |
|---|---|---|---|
| `GET /` | None | Object with `app: str`, `version: str`, `ip: str`, `uptime: number` (observed) | OpenAPI documents `200`; no error response documented |
| `GET /nyaa` | Optional query: `q`, `category`, `sub_category`, `sort`, `order` strings; `page` integer, default `1` | `{ "count": int, "data": Torrent[] }` (observed) | OpenAPI `422` validation error; observed `200` |
| `GET /sukebei` | Same as `/nyaa` | Same search envelope | OpenAPI `422`; observed `200` |
| `GET /nyaa/user/{user_name}` | Required path `user_name: str`; same optional query parameters as `/nyaa` | Same search envelope | OpenAPI `422`; observed `200` |
| `GET /sukebei/user/{user_name}` | Required path `user_name: str`; same optional query parameters | Same search envelope | OpenAPI `422`; observed `200`; page 2 for tested uploader returned `404` |
| `GET /nyaa/id/{torrent_id}` | Required path `torrent_id: int` | `{ "data": TorrentDetail }` | OpenAPI `422`; observed `200` |
| `GET /sukebei/id/{torrent_id}` | Required path `torrent_id: int` | `{ "data": TorrentDetail }` | OpenAPI `422`; tested ID `1234567` returned `404` with `{ "detail": "Invalid torrent ID." }` |

OpenAPI defines no `enum` constraints for category, sub-category, sort, or order. It describes order as `asc` or `desc` but does not encode that as a schema constraint. No category list or allowed sort list is exposed. These values are passed through as strings. Search parameter names are exactly `q`, `category`, `sub_category`, `sort`, `order`, and `page`.

The OpenAPI success response schemas are empty (`{}`), so torrent fields below come from actual responses, not from the schema. Search results contain `category`, `title`, `link`, `torrent`, `magnet`, `size`, `time`, `seeders`, `leechers`, and `downloads`. Detail data additionally contains `uploader`, `information`, `infohash`, and `comments`; comments observed contain `user`, `profileUrl`, `avatar`, `commentBody`, `time`, and `link`. All values above were present in the captured samples; the implementation treats detail-only fields as optional when parsing search rows.

## Pagination and observations

`page` is an optional integer query parameter whose documented default is 1. A live Nyaa search returned 75 rows on pages 1, 2, and 3. Another live Sukebei uploader query returned 62 rows. A distinctive no-match search returned `{ "count": 0, "data": [] }`. Thus 75 rows is a maximum observed page size, not an authoritative constant for every page or source. OpenAPI has no `has_next` field. The client advances page numbers and stops on an empty page or a page containing no unseen torrent links; it does not infer that a short page is necessarily final.

The `count` property matched the row count in the sampled responses and is modeled as the count returned by that response. Its global-versus-per-page meaning is not specified by OpenAPI. A request to `/sukebei/user/Tsundere-Raws?page=2` returned `404`; this is recorded as observed service behavior, not generalized as an API guarantee. Date strings in search rows had no timezone suffix, while detail and comment dates used ` UTC`; parsed search datetimes are therefore naive and detail datetimes UTC-aware.

OpenAPI documents only `200`/`422` for the applicable operations (and only `200` for `/`). Other HTTP errors are not specified. Observed: the invalid Sukebei ID returned `404`; the tested Sukebei uploader page 2 also returned `404`. The home endpoint returned the service name/version, an IP address, and uptime. No separate category endpoint exists.
