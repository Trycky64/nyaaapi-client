import os

import pytest

from nyaaapi import NyaaAPI

RUN_INTEGRATION = os.environ.get("NYAAAPI_RUN_INTEGRATION") == "1"


@pytest.mark.integration
@pytest.mark.skipif(
    not RUN_INTEGRATION,
    reason="set NYAAAPI_RUN_INTEGRATION=1 to contact the live service",
)
def test_live_home_and_empty_search() -> None:
    with NyaaAPI(timeout=60) as api:
        home = api.home()
        results = api.search("nyaaapi-client-no-match-20261005-unique")
    assert home.app == "Nyaa API"
    assert results.data == ()
