"""Reporter benchmark-performance tests.

Agent: reporter
Role: prove date-bounded performance projections from graph facts.
External I/O: none.
"""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

import pytest

from kernel import InMemoryGraphStore

if TYPE_CHECKING:
    from collections.abc import Sequence

    from agents.reporter.performance_inputs import PerformanceInputs

_INCEPTION = date(2026, 8, 10)
_AS_OF = "2026-08-12T22:30:00+00:00"


def test_performance_worked_example() -> None:
    """RPT-OUT-07: chained book, benchmark, and exposure returns agree exactly."""
    metrics = _calculate_performance(
        [
            (date(2026, 8, 10), 1_000_000, 500_000),
            (date(2026, 8, 11), 1_010_000, 505_000),
            (date(2026, 8, 12), 999_900, 0),
        ],
        {
            date(2026, 8, 10): 100.0,
            date(2026, 8, 11): 102.0,
            date(2026, 8, 12): 101.0,
        },
    )

    assert metrics["portfolio_return_pct"] == pytest.approx(-0.01)
    assert metrics["benchmark_return_pct"] == pytest.approx(1.0)
    assert metrics["exposure_matched_return_pct"] == pytest.approx(0.504902)
    assert metrics["excess_return_pct"] == pytest.approx(-0.514902)
    assert metrics["average_exposure_pct"] == pytest.approx(50.0)
    assert metrics["max_drawdown_pct"] == pytest.approx(-1.0)
    assert metrics["performance_sessions"] == 2.0


def test_performance_inputs_do_not_read_after_pmrun_as_of() -> None:
    """RPT-IDM-03: re-reporting ignores every snapshot and bar after PMRun as-of."""
    bounded = _read_performance_inputs(_seed_graph(include_future=True))
    baseline = _read_performance_inputs(_seed_graph(include_future=False))

    assert bounded.points == baseline.points
    assert bounded.benchmark_closes == baseline.benchmark_closes
    assert max(point[0] for point in bounded.points) == date(2026, 8, 12)


def test_performance_inputs_exclude_pre_inception_margin_book() -> None:
    """RPT-OUT-07: pre-inception negative cash and leveraged holdings are excluded."""
    inputs = _read_performance_inputs(
        _seed_graph(include_future=False, include_pre=True)
    )
    metrics = _calculate_performance(inputs.points, inputs.benchmark_closes)

    assert min(point[0] for point in inputs.points) == _INCEPTION
    assert metrics["max_drawdown_pct"] == 0.0
    assert metrics["average_exposure_pct"] == pytest.approx(50.0)


def _calculate_performance(
    points: Sequence[tuple[date, int, int]], benchmark_closes: dict[date, float]
) -> dict[str, float]:
    from agents.reporter.domain.performance import calculate_performance

    return calculate_performance(points, benchmark_closes, rolling_sessions=20)


def _read_performance_inputs(graph: InMemoryGraphStore) -> PerformanceInputs:
    from agents.reporter.performance_inputs import read_performance_inputs

    pm_run = graph.get_node("PMRun", "pm-run-performance")
    assert pm_run is not None
    return read_performance_inputs(graph, pm_run, inception=_INCEPTION)


def _seed_graph(
    *, include_future: bool, include_pre: bool = False
) -> InMemoryGraphStore:
    graph = InMemoryGraphStore()
    graph.merge_node("PMRun", "pm-run-performance", {"created_at": _AS_OF})
    if include_pre:
        _snapshot(
            graph,
            "2026-08-09",
            equity_cents=10_315_000,
            long_value_cents=20_811_700,
            cash_cents=-10_496_700,
        )
    _snapshot(graph, "2026-08-10", equity_cents=1_000_000, long_value_cents=500_000)
    _snapshot(graph, "2026-08-11", equity_cents=1_010_000, long_value_cents=505_000)
    _snapshot(graph, "2026-08-12", equity_cents=1_010_000, long_value_cents=0)
    if include_future:
        _snapshot(graph, "2026-08-13", equity_cents=800_000, long_value_cents=800_000)

    graph.merge_node(
        "MarketData",
        "market-data:bounded",
        {
            "window_end": "2026-08-12",
            "snapshot": {"benchmark": _benchmark_bars(include_future=False)},
        },
    )
    if include_future:
        graph.merge_node(
            "MarketData",
            "market-data:future",
            {
                "window_end": "2026-08-13",
                "snapshot": {"benchmark": _benchmark_bars(include_future=True)},
            },
        )
    return graph


def _snapshot(
    graph: InMemoryGraphStore,
    day: str,
    *,
    equity_cents: int,
    long_value_cents: int,
    cash_cents: int = 0,
) -> None:
    graph.merge_node(
        "BrokerPositionSnapshot",
        f"broker-position-snapshot:{day}",
        {
            "status": "fresh",
            "account_status": "fresh",
            "created_at": f"{day}T22:30:00+00:00",
            "account_equity_cents": equity_cents,
            "account_cash_cents": cash_cents,
            "holdings": [{"market_value_cents": long_value_cents}],
        },
    )


def _benchmark_bars(*, include_future: bool) -> list[dict[str, object]]:
    bars: list[dict[str, object]] = [
        {"ticker": "SPY", "bar_date": "2026-08-10", "close": 100.0},
        {"ticker": "SPY", "bar_date": "2026-08-11", "close": 102.0},
        {"ticker": "SPY", "bar_date": "2026-08-12", "close": 101.0},
    ]
    if include_future:
        bars[-1]["close"] = 90.0
        bars.append({"ticker": "SPY", "bar_date": "2026-08-13", "close": 90.0})
    return bars
