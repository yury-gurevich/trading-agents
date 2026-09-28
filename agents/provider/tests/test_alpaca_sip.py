"""Alpaca SIP request tests: the query the source sends, and a refusal.

Agent: provider
Role: verify the bars query the source hands its page download: a SIP request
never ends inside the plan's recent-data wall, an IEX request is the query the
source always sent, pages follow their token, and a refused request raises.
External I/O: none (the page download is stubbed; no test reaches the network).
"""

from __future__ import annotations

import urllib.error
import urllib.parse
from datetime import UTC, date, datetime
from email.message import Message
from types import MethodType

import pytest

from agents.provider.alpaca_data import AlpacaDataSource
from contracts.common import Window

_TODAY = Window(start=date(2026, 9, 1), end=date(2026, 9, 28))
_JAN = Window(start=date(2026, 1, 1), end=date(2026, 1, 31))
_JAN_10 = "2026-01-10T05:00:00Z"


def _bar(stamp: str) -> str:
    return f'{{"t":"{stamp}","o":10.0,"h":11.0,"l":9.0,"c":10.5,"v":3019571}}'


def _source(feed: str, now: datetime) -> AlpacaDataSource:
    return AlpacaDataSource(
        api_key="k",
        api_secret="s",  # noqa: S106 - test stub credential, not a real secret.
        base_url="https://alpaca.test",
        feed=feed,
        timeout=10,
        clock=lambda: now,
    )


def _record(source: AlpacaDataSource, pages: list[str]) -> list[dict[str, str]]:
    """Stub the page download: record each query, answer from ``pages``."""
    sent: list[dict[str, str]] = []

    def fake_page(_self: AlpacaDataSource, query: dict[str, str]) -> str:
        sent.append(dict(query))
        return pages[len(sent) - 1]

    source._download_page = MethodType(fake_page, source)  # type: ignore[method-assign]
    return sent


def test_sip_request_for_a_window_ending_today_ends_clear_of_the_wall() -> None:
    """PROV-OUT-07: a SIP request never asks for the last 15 minutes (it keeps a
    one-minute clock margin: Alpaca refuses 899 s and serves 900 s, measured), and the
    session's own bar (stamped 04:00Z) still falls inside what it asks for."""
    now = datetime(2026, 9, 28, 22, 30, tzinfo=UTC)
    source = _source("sip", now)
    rows = f"{_bar('2026-09-25T04:00:00Z')},{_bar('2026-09-28T04:00:00Z')}"
    payload = f'{{"bars":{{"LLY":[{rows}]}}}}'
    sent = _record(source, [payload])
    bars = source.fetch_ohlcv(("LLY",), _TODAY)
    assert len(sent) == 1
    assert sent[0]["feed"] == "sip"
    assert sent[0]["end"] == "2026-09-28T22:14:00Z"
    end = datetime.fromisoformat(sent[0]["end"].replace("Z", "+00:00"))
    assert datetime(2026, 9, 28, 4, tzinfo=UTC) < end
    assert date(2026, 9, 28) in {bar.bar_date for bar in bars}
    assert {bar.volume for bar in bars} == {3019571}


@pytest.mark.parametrize(
    "now",
    [
        datetime(2026, 1, 31, 12, 0, tzinfo=UTC),
        datetime(2026, 2, 1, 12, 0, tzinfo=UTC),
    ],
)
def test_iex_request_is_the_query_the_source_always_sent(now: datetime) -> None:
    """PROV-OUT-07: the clamp is SIP's alone; an IEX query is unchanged, key for
    key and byte for byte once encoded, on every page, whatever the clock."""
    source = _source("iex", now)
    sent = _record(
        source,
        [
            f'{{"bars":{{"AAPL":[{_bar(_JAN_10)}]}},"next_page_token":"tok"}}',
            f'{{"bars":{{"MSFT":[{_bar(_JAN_10)}]}},"next_page_token":null}}',
        ],
    )
    bars = source.fetch_ohlcv(("AAPL", "MSFT"), _JAN)
    first = {
        "symbols": "AAPL,MSFT",
        "timeframe": "1Day",
        "start": "2026-01-01",
        "end": "2026-01-31",
        "feed": "iex",
        "limit": "10000",
    }
    assert list(sent[0].items()) == list(first.items())
    assert list(sent[1].items()) == [*first.items(), ("page_token", "tok")]
    encoded = urllib.parse.urlencode(sent[1])
    assert encoded == (
        "symbols=AAPL%2CMSFT&timeframe=1Day&start=2026-01-01&end=2026-01-31"
        "&feed=iex&limit=10000&page_token=tok"
    )
    assert sorted(bar.ticker for bar in bars) == ["AAPL", "MSFT"]


def test_refused_sip_request_raises_and_never_asks_another_feed() -> None:
    """PROV-OUT-07 / PROV-FAIL-01: a 403 reaches the provider's fault boundary
    as a raise - never an empty success, never a second request on IEX."""
    source = _source("sip", datetime(2026, 9, 28, 22, 30, tzinfo=UTC))
    sent: list[dict[str, str]] = []

    def refused(_self: AlpacaDataSource, query: dict[str, str]) -> str:
        sent.append(dict(query))
        raise urllib.error.HTTPError(
            "https://alpaca.test/v2/stocks/bars", 403, "Forbidden", Message(), None
        )

    source._download_page = MethodType(refused, source)  # type: ignore[method-assign]
    with pytest.raises(urllib.error.HTTPError):
        source.fetch_ohlcv(("LLY",), _TODAY)
    assert [query["feed"] for query in sent] == ["sip"]


def test_default_clock_is_aware_utc() -> None:
    """PROV-OUT-07: without an injected clock the source reads real UTC time."""
    source = AlpacaDataSource(
        api_key="k",
        api_secret="s",  # noqa: S106 - test stub credential, not a real secret.
        base_url="https://alpaca.test",
        feed="sip",
        timeout=10,
    )
    before = datetime.now(UTC)
    now = source._clock()
    assert now.tzinfo is not None
    assert before <= now <= datetime.now(UTC)
