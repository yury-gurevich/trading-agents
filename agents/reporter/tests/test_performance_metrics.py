"""Pure reporter performance calculation tests.

Agent: reporter
Role: prove metric behavior without graph or bus dependencies.
External I/O: none.
"""

from __future__ import annotations

import subprocess
import sys
from datetime import date, timedelta

import pytest

from agents.reporter.domain.performance import calculate_performance


def test_performance_skips_missing_benchmark_pair_then_continues() -> None:
    """RPT-OUT-07: a benchmark gap is counted and later usable pairs still chain."""
    points = [
        (date(2026, 8, 10), 1_000_000, 500_000),
        (date(2026, 8, 11), 1_100_000, 550_000),
        (date(2026, 8, 12), 1_210_000, 605_000),
    ]
    metrics = calculate_performance(
        points,
        {date(2026, 8, 11): 100.0, date(2026, 8, 12): 110.0},
        rolling_sessions=20,
    )

    assert metrics["performance_gap_sessions"] == 1.0
    assert metrics["performance_sessions"] == 1.0
    assert metrics["portfolio_return_pct"] == pytest.approx(10.0)


def test_performance_returns_zero_when_no_pair_is_usable() -> None:
    """RPT-NEV-03: fewer than one usable pair produces a defined zero metric set."""
    metrics = calculate_performance(
        [(date(2026, 8, 10), 1_000_000, 500_000)],
        {date(2026, 8, 10): 100.0},
        rolling_sessions=20,
    )

    assert set(metrics.values()) == {0.0}


def test_performance_rolling_metrics_use_only_last_configured_pairs() -> None:
    """RPT-OUT-07: rolling return metrics use exactly the configured last pairs."""
    start = date(2026, 8, 10)
    points = [
        (start + timedelta(days=index), 1_000_000 + index * 10_000, 500_000)
        for index in range(26)
    ]
    closes = {point[0]: 100.0 + index for index, point in enumerate(points)}

    metrics = calculate_performance(points, closes, rolling_sessions=20)

    assert metrics["performance_sessions"] == 25.0
    assert metrics["portfolio_return_pct"] == pytest.approx(25.0)
    assert metrics["rolling_portfolio_return_pct"] == pytest.approx(19.047619)
    assert metrics["rolling_excess_return_pct"] != metrics["excess_return_pct"]


def test_performance_zero_equity_point_does_not_break_drawdown() -> None:
    """RPT-OUT-07: a zero-equity point is skipped but drawdown remains defined."""
    metrics = calculate_performance(
        [
            (date(2026, 8, 10), 0, 0),
            (date(2026, 8, 11), 100_000, 10_000),
            (date(2026, 8, 12), 90_000, 9_000),
        ],
        {
            date(2026, 8, 10): 100.0,
            date(2026, 8, 11): 100.0,
            date(2026, 8, 12): 100.0,
        },
        rolling_sessions=20,
    )

    assert metrics["performance_sessions"] == 1.0
    assert metrics["performance_gap_sessions"] == 1.0
    assert metrics["max_drawdown_pct"] == pytest.approx(-10.0)


def test_performance_calculator_import_is_pure() -> None:
    """RPT-OUT-07: calculator import loads no graph, bus, or reporter-store module."""
    script = """
import sys
from agents.reporter.domain.performance import calculate_performance
forbidden = [
    name for name in sys.modules
    if name.startswith(("kernel.graph", "kernel.bus", "agents.reporter.store"))
]
assert forbidden == [], forbidden
assert callable(calculate_performance)
"""
    completed = subprocess.run(  # noqa: S603 - fixed interpreter and import probe.
        [sys.executable, "-c", script], check=False, capture_output=True, text=True
    )

    assert completed.returncode == 0, completed.stderr
