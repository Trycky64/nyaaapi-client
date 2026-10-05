import json
from pathlib import Path
from typing import Any

from nyaaapi import HomeInfo, SearchResults, TorrentDetails

FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> dict[str, Any]:
    return json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))


def test_search_model_uses_captured_response() -> None:
    results = SearchResults.from_dict(load_fixture("search"))
    assert results.count == 75
    assert len(results) == 75
    assert next(iter(results)).title.startswith("Mushoku Tensei")


def test_empty_search_model() -> None:
    results = SearchResults.from_dict(load_fixture("empty"))
    assert results.count == 0
    assert len(results) == 0


def test_detail_model_includes_comments_and_utc_time() -> None:
    detail = TorrentDetails.from_dict(load_fixture("detail")).data
    assert detail.uploader == "Judas"
    assert detail.infohash
    assert detail.comments is not None
    assert detail.comments[0].time is not None
    assert detail.comments[0].time.utcoffset().total_seconds() == 0


def test_home_model_uses_observed_fields() -> None:
    home = HomeInfo.from_dict(load_fixture("home"))
    assert home.app == "Nyaa API"
    assert home.version == "2.0.1"
