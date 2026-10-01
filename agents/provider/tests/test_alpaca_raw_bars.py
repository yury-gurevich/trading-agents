"""The bars the provider serves are raw: its request asks for no adjustment (S251 D5).

Agent: provider
Role: pin the query the Alpaca source sends, on every page and for both feeds, to
      exactly the keys it has always sent - none of them a price adjustment, so the
      source serves its default, raw (unadjusted) bars (DRIFT-084, DL-260).
External I/O: none (the page download is stubbed; no test reaches the network).
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from agents.provider.tests.test_alpaca_sip import _JAN, _JAN_10, _bar, _record, _source

_SENT_KEYS = {"symbols", "timeframe", "start", "end", "feed", "limit"}


@pytest.mark.parametrize("feed", ["sip", "iex"])
def test_the_bars_request_asks_for_no_price_adjustment(feed: str) -> None:
    """PROV-OUT-07 (DRIFT-084): every page the source requests carries only the
    symbols, timeframe, window, feed, limit and page token, so no split or dividend
    adjustment is ever asked for and a bar's prices are as they traded."""
    source = _source(feed, datetime(2026, 2, 1, 12, 0, tzinfo=UTC))
    sent = _record(
        source,
        [
            f'{{"bars":{{"AAPL":[{_bar(_JAN_10)}]}},"next_page_token":"tok"}}',
            f'{{"bars":{{"AAPL":[{_bar(_JAN_10)}]}},"next_page_token":null}}',
        ],
    )

    bars = source.fetch_ohlcv(("AAPL",), _JAN)

    assert [set(query) - {"page_token"} for query in sent] == [_SENT_KEYS] * 2
    assert not [key for query in sent for key in query if "adjust" in key.lower()]
    assert {bar.close for bar in bars} == {10.5}
