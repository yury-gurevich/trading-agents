"""Provider earnings-horizon declaration tests (S196).

Agent: provider
Role: verify the provider states how far its earnings map reaches, and withholds
      that claim whenever the feed was not requested or came back degraded.
External I/O: none.
"""

from __future__ import annotations

from datetime import date

from agents.provider import ProviderAgent
from agents.provider.ingest_chunked import _merged_earnings_horizon
from agents.provider.settings import ProviderSettings
from agents.provider.sources import FakeDataSource
from contracts.common import Provenance, Window
from contracts.provider import DataQualityTrace, DataRequest, MarketData
from kernel import InMemoryGraphStore, InProcessBus

_WINDOW = Window(start=date(2026, 1, 2), end=date(2026, 1, 6))
_FIELDS = ("ohlcv", "earnings_calendar")


def _market(source: FakeDataSource, fields: tuple[str, ...] = _FIELDS) -> MarketData:
    agent = ProviderAgent(InProcessBus(), graph=InMemoryGraphStore(), source=source)
    return agent._get_market_data(
        DataRequest(tickers=("AAPL",), window=_WINDOW, fields=fields)
    )


def test_a_clean_earnings_fetch_declares_the_settings_horizon() -> None:
    """The map is complete for the lookahead the provider actually queried."""
    market = _market(FakeDataSource(earnings={"AAPL": date(2026, 1, 20)}))
    assert (
        market.earnings_horizon_days
        == ProviderSettings().finnhub_earnings_lookahead_days
    )


def test_an_empty_but_clean_earnings_fetch_still_declares_the_horizon() -> None:
    """No dates due is the common case, and it is an answer — not a gap."""
    market = _market(FakeDataSource(earnings={}))
    assert market.earnings_horizon_days is not None
    assert market.earnings == {}


def test_an_unrequested_earnings_feed_declares_nothing() -> None:
    market = _market(FakeDataSource(earnings={"AAPL": date(2026, 1, 20)}), ("ohlcv",))
    assert market.earnings_horizon_days is None


def test_a_degraded_earnings_feed_withholds_the_horizon() -> None:
    """A failed fetch leaves gaps that look exactly like 'no earnings due'."""
    market = _market(FakeDataSource(fail_earnings=True))
    assert market.earnings_horizon_days is None
    assert any(note.startswith("earnings_degraded") for note in market.quality.notes)


def _part(horizon: int | None) -> MarketData:
    return MarketData(
        bars=(),
        earnings_horizon_days=horizon,
        quality=DataQualityTrace(requested=0, returned=0),
        provenance=Provenance(run_id="p", source_agent="provider"),
    )


def test_chunked_merge_keeps_a_horizon_every_chunk_agrees_on() -> None:
    assert _merged_earnings_horizon((_part(30), _part(30))) == 30


def test_chunked_merge_drops_the_horizon_when_one_chunk_degraded() -> None:
    """The batch is one unit downstream, so one bad chunk taints the claim."""
    assert _merged_earnings_horizon((_part(30), _part(None))) is None
