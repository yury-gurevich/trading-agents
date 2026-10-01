"""A run's ingest serves the run's own as-of, whenever the provider reaches it (S249).

Agent: provider
Role: prove PROV-TRG-05 on both ingest paths: the market window ends on the
      RunRequest's as-of and starts the declared lookback before it, the regime is
      read as of it, news and earnings anchor on it; an as-of of today, and an
      ingest with no run, still serve today's window.
External I/O: none.
"""

from __future__ import annotations

from datetime import UTC, date, datetime

from agents.provider.ingest import _today_window, ingest_once
from agents.provider.poll import ingest_run_node
from agents.provider.settings import ProviderSettings
from agents.provider.tests.as_of_helpers import (
    RecordingFinnhub,
    RecordingSource,
    agent_over,
    run_request,
    window_ends,
)
from contracts.common import Window
from contracts.provider import MARKET_DATA_LABEL, REGIME_CONTEXT_LABEL
from kernel import InMemoryGraphStore

# A fixed past session: on any day but this one the clock's window differs from it.
_AS_OF = "2026-09-30"
_SERVED = Window(start=date(2025, 9, 30), end=date(2026, 9, 30))


def test_a_runs_market_window_ends_on_its_as_of() -> None:
    """PROV-TRG-05: the window ends on the as-of and starts the lookback before it."""
    graph = InMemoryGraphStore()
    source = RecordingSource()
    ingest_run_node(run_request(graph, _AS_OF), agent=agent_over(graph, source))

    assert source.ohlcv_windows == [_SERVED]
    assert window_ends(graph)[0] == "2026-09-30"


def test_the_regime_is_read_as_of_the_runs_as_of() -> None:
    """PROV-TRG-05: the regime source is asked for the as-of, and stores it."""
    graph = InMemoryGraphStore()
    source = RecordingSource()
    ingest_run_node(run_request(graph, _AS_OF), agent=agent_over(graph, source))

    assert source.regime_dates == [date(2026, 9, 30)]
    assert window_ends(graph)[1] == "2026-09-30"
    regime = graph.get_node(REGIME_CONTEXT_LABEL, "regime-context:r1")
    assert regime is not None
    assert str(regime.props["snapshot"]["as_of"]).startswith("2026-09-30")


def test_the_chunked_path_serves_the_same_as_of() -> None:
    """PROV-TRG-05: every chunk: the as-of's window; the one MarketData ends on it."""
    graph = InMemoryGraphStore()
    source = RecordingSource()
    settings = ProviderSettings(ingest_chunk_size=1, ingest_chunk_delay_seconds=0.0)
    ingest_run_node(
        run_request(graph, _AS_OF, tickers=("AAPL", "MSFT", "TGT")),
        agent=agent_over(graph, source, settings),
    )

    assert source.ohlcv_windows == [_SERVED, _SERVED, _SERVED]
    assert source.regime_dates == [date(2026, 9, 30)]
    assert len(graph.list_nodes(MARKET_DATA_LABEL)) == 1
    assert window_ends(graph) == ("2026-09-30", "2026-09-30")


def test_news_and_earnings_are_anchored_on_the_as_of() -> None:
    """PROV-TRG-05: news windows end on the as-of; earnings windows start on it."""
    graph = InMemoryGraphStore()
    source = RecordingFinnhub(news_lookback_days=7)
    ingest_run_node(run_request(graph, _AS_OF), agent=agent_over(graph, source))

    assert source.asked["news"] == (date(2026, 9, 23), date(2026, 9, 30))
    assert source.asked["earnings"][0] == date(2026, 9, 30)


def test_a_run_whose_as_of_is_today_is_unchanged() -> None:
    """PROV-TRG-05: a run for today (a scheduled run) serves today's window exactly."""
    graph = InMemoryGraphStore()
    source = RecordingSource()
    today = datetime.now(tz=UTC).date()
    ingest_run_node(
        run_request(graph, today.isoformat()), agent=agent_over(graph, source)
    )

    assert source.ohlcv_windows == [_today_window(365)]
    assert source.regime_dates == [today]


def test_an_ingest_with_no_run_keeps_todays_window() -> None:
    """PROV-TRG-05: an ingest no RunRequest triggered serves today, as before."""
    graph = InMemoryGraphStore()
    source = RecordingSource()
    ingest_once(agent_over(graph, source), ("AAPL",), lookback_days=30)

    assert source.ohlcv_windows == [_today_window(30)]
    assert source.regime_dates == [datetime.now(tz=UTC).date()]
