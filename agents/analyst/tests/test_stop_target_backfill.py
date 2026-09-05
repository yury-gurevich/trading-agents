"""Realized-drawdown backfill tests (graph read/write path).

Agent: analyst
Role: prove the run records what its bars can settle, and never guesses the rest.
External I/O: none.
"""

from __future__ import annotations

from datetime import date, timedelta
from types import SimpleNamespace
from typing import TYPE_CHECKING, cast

from agents.analyst.outcome_backfill import (
    DRAWDOWN_PROP,
    HORIZON_PROP,
    backfill_observed_drawdowns,
)
from agents.analyst.run import _record_settled_drawdowns
from agents.analyst.settings import AnalystSettings
from contracts.provider import OHLCVBar
from kernel import CollectingFaultSink, InMemoryGraphStore

if TYPE_CHECKING:
    from contracts.provider import MarketData
    from kernel import GraphStore

_DECISION = date(2026, 3, 2)


def test_backfill_writes_the_drawdown_and_horizon_onto_a_settled_recommendation() -> (
    None
):
    """ANLZ-OBS-05: the run records what its own bars can settle."""
    graph = _graph_with_recommendation("AAA")
    bars = (*_flat("AAA", days=1, close=100.0), *_lows("AAA", (98.0, 91.0, 95.0)))

    assert backfill_observed_drawdowns(graph, bars, horizon_days=3) == 1

    props = graph.list_nodes("Recommendation")[0].props
    assert props[DRAWDOWN_PROP] == 0.09
    assert props[HORIZON_PROP] == 3


def test_a_recorded_drawdown_is_never_rewritten() -> None:
    """ANLZ-OBS-05: the merge is append-only, so an observation is immutable."""
    graph = _graph_with_recommendation("AAA", extra={DRAWDOWN_PROP: 0.02})
    bars = (*_flat("AAA", days=1, close=100.0), *_lows("AAA", (98.0, 91.0, 95.0)))

    assert backfill_observed_drawdowns(graph, bars, horizon_days=3) == 0
    assert graph.list_nodes("Recommendation")[0].props[DRAWDOWN_PROP] == 0.02


def test_an_unsettled_recommendation_is_left_without_the_property() -> None:
    """ANLZ-OBS-05: absence means the window has not settled, not that it fell zero."""
    graph = _graph_with_recommendation("AAA")
    bars = (*_flat("AAA", days=1, close=100.0), *_lows("AAA", (98.0,)))

    assert backfill_observed_drawdowns(graph, bars, horizon_days=3) == 0
    assert DRAWDOWN_PROP not in graph.list_nodes("Recommendation")[0].props


def test_a_ticker_the_run_never_fetched_is_skipped() -> None:
    """ANLZ-OBS-05: the backfill measures only what this run's bars cover."""
    graph = _graph_with_recommendation("AAA")
    bars = (*_flat("BBB", days=1, close=100.0), *_lows("BBB", (90.0, 90.0, 90.0)))

    assert backfill_observed_drawdowns(graph, bars, horizon_days=3) == 0


def test_a_run_with_no_bars_writes_nothing() -> None:
    """ANLZ-OBS-05: a degraded run must not be read as a book of zero drawdowns."""
    graph = _graph_with_recommendation("AAA")

    assert backfill_observed_drawdowns(graph, (), horizon_days=3) == 0


def test_unreadable_lineage_is_skipped_rather_than_guessed() -> None:
    """ANLZ-OBS-05: no decision day and no ticker string means no measurement."""
    graph = InMemoryGraphStore()
    graph.merge_node("AnalystRun", "run-bad", {"created_at": "not-a-timestamp"})
    graph.merge_node("AnalystRun", "run-typed", {"created_at": 20260302})
    graph.merge_node("Recommendation", "run-bad:AAA", {"ticker": "AAA"})
    graph.merge_node("Recommendation", "run-typed:AAA", {"ticker": "AAA"})
    graph.merge_node("Recommendation", "run-missing:AAA", {"ticker": 7})
    bars = (*_flat("AAA", days=1, close=100.0), *_lows("AAA", (98.0, 91.0, 95.0)))

    assert backfill_observed_drawdowns(graph, bars, horizon_days=3) == 0


def test_a_backfill_failure_is_a_fault_and_does_not_withdraw_the_run() -> None:
    """ANLZ-OBS-05 / ANLZ-OBS-02: the recommendations are already written."""
    sink = CollectingFaultSink()

    class _Unreadable:
        def list_nodes(self, label: str) -> tuple[object, ...]:
            raise RuntimeError(f"graph unavailable for {label}")

    market = SimpleNamespace(bars=(_bar("AAA", _DECISION, 100.0, 100.0),))

    _record_settled_drawdowns(
        cast("GraphStore", _Unreadable()),
        cast("MarketData", market),
        AnalystSettings(),
        sink,
    )

    assert len(sink.faults) == 1


def _graph_with_recommendation(
    ticker: str, *, extra: dict[str, object] | None = None
) -> InMemoryGraphStore:
    graph = InMemoryGraphStore()
    graph.merge_node(
        "AnalystRun", "run-1", {"created_at": f"{_DECISION.isoformat()}T22:30:00+00:00"}
    )
    graph.merge_node(
        "Recommendation", f"run-1:{ticker}", {"ticker": ticker, **(extra or {})}
    )
    return graph


def _flat(ticker: str, *, days: int, close: float) -> tuple[OHLCVBar, ...]:
    return tuple(
        _bar(ticker, _DECISION - timedelta(days=offset), close, close)
        for offset in range(days)
    )


def _lows(ticker: str, lows: tuple[float, ...]) -> tuple[OHLCVBar, ...]:
    return tuple(
        _bar(ticker, _DECISION + timedelta(days=index + 1), max(low, 100.0), low)
        for index, low in enumerate(lows)
    )


def _bar(ticker: str, day: date, close: float, low: float) -> OHLCVBar:
    return OHLCVBar(
        ticker=ticker,
        bar_date=day,
        open=close,
        high=max(close, low) + 1.0,
        low=low,
        close=close,
        volume=1_000_000,
    )
