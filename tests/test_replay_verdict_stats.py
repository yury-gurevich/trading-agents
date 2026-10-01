"""S250: the scorer's returns, rebuilds, draws and yearly windows.

Agent: tooling
Role: prove every return is the reporter's, and the bootstrap's pieces are faithful.
External I/O: none.
"""

from __future__ import annotations

import math
from datetime import date
from itertools import pairwise
from typing import Any

import pytest
from scripts.replay_verdict_score import score_arms
from scripts.replay_verdict_stats import (
    arm_pairs,
    percentile_interval,
    performance,
    rebuild,
    seeded,
    stationary_draws,
)
from scripts.replay_verdict_windows import year_windows
from tests.replay_verdict_fixtures import (
    five_arms,
    spy_closes,
    synthetic_arm,
    trading_days,
)

STUB = {
    "portfolio_return_pct": 10.0,
    "benchmark_return_pct": 7.0,
    "exposure_matched_return_pct": 5.0,
    "excess_return_pct": 5.0,
    "average_exposure_pct": 80.0,
    "max_drawdown_pct": -3.0,
    "rolling_portfolio_return_pct": 1.0,
    "rolling_exposure_matched_return_pct": 1.0,
    "rolling_excess_return_pct": 0.0,
    "performance_sessions": 252.0,
    "performance_gap_sessions": 0.0,
    "equity_cents": 1.0,
}
STUB_A = (1.10 - 1.05) * 100  # 252 / n = 1, so A is P - E


def test_c5_every_return_comes_from_calculate_performance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """S250-C5 / RPT-OUT-07: headline, years, halves and every draw are the stub's.

    The reporter's function is replaced by a stub with fixed outputs. If any number
    in the scorer came from anywhere else (a ratio chained by hand), it would not be
    5.0, and the call count would fall short of one call per window and per draw.
    """
    calls: list[int] = []

    def stub(points: Any, closes: Any, *, rolling_sessions: int) -> dict[str, float]:
        del points, closes
        calls.append(rolling_sessions)
        return dict(STUB)

    monkeypatch.setattr("scripts.replay_verdict_stats.calculate_performance", stub)
    arms = five_arms(0.0, 0.0, count=61)

    scored = score_arms(arms, resamples=40, mean_block=5, seed=0)

    windows = 0
    for arm in scored["arms"].values():
        rows = [arm["whole"], *arm["years"], *arm["halves"]]
        windows += len(rows)
        for row in rows:
            assert row["portfolio_return_pct"] == STUB["portfolio_return_pct"]
            assert row["annualised_excess_pts"] == pytest.approx(STUB_A, abs=1e-12)
        assert arm["interval"] == pytest.approx([STUB_A, STUB_A], abs=1e-12)
    for difference in scored["differences"].values():
        assert difference["point"] == pytest.approx(0.0, abs=1e-12)
        assert difference["interval"] == pytest.approx([0.0, 0.0], abs=1e-12)
    control = scored["control"]
    assert control["annualised_excess_pts"] == pytest.approx(STUB_A, abs=1e-12)
    assert len(calls) == windows + len(arms) * 40 + 1 + 40
    assert set(calls) == {20}
    assert scored["verdict"] is None
    assert [item["arm"] for item in scored["refusals"]] == ["control"]


def test_c7_a_rebuilt_series_is_faithful() -> None:
    """S250-C7 / RPT-OUT-07: rebuilt in original order, P, E and n are unchanged."""
    closes = spy_closes(trading_days(date(2017, 1, 3), 400), seed=3)
    arm = synthetic_arm("base-25", closes, drift=0.0004, seed=5)
    original = performance(arm.points, arm.closes)

    pairs = arm_pairs(arm.points, arm.closes)
    points, rebuilt_closes = rebuild(pairs, range(len(pairs)))
    again = performance(points, rebuilt_closes)

    assert len(pairs) == len(arm.points) - 1
    for key in ("portfolio_return_pct", "exposure_matched_return_pct"):
        assert again[key] == pytest.approx(original[key], abs=1e-9)
    assert again["performance_sessions"] == original["performance_sessions"] == 399.0


def test_c8_the_bootstrap_is_seeded_and_blocked() -> None:
    """S250-C8: same seed, same draws; full length; wrapping runs near the block."""
    n, block = 500, 20

    def draws(seed: int, count: int) -> list[list[int]]:
        rng = seeded(seed)
        return [stationary_draws(n, block, rng) for _ in range(count)]

    first, again, other = draws(0, 200), draws(0, 200), draws(1, 200)

    assert first == again
    assert first != other
    runs: list[int] = []
    for resample in first:
        assert len(resample) == n
        assert all(0 <= index < n for index in resample)
        length = 1
        for previous, current in pairwise(resample):
            if current == (previous + 1) % n:
                length += 1
            else:
                runs.append(length)
                length = 1
        runs.append(length)
    wrapped = sum(
        1
        for resample in first
        for previous, current in pairwise(resample)
        if previous == n - 1 and current == 0
    )
    assert 17.0 <= sum(runs) / len(runs) <= 23.0
    assert wrapped > 0


def test_c8_the_percentiles_are_order_statistics() -> None:
    """S250-C8: k = B * 25 // 1000; the interval is v[k] and v[B - 1 - k]."""
    values = [float(value) for value in reversed(range(10_000))]
    assert percentile_interval(values) == (250.0, 9749.0)
    assert percentile_interval([float(v) for v in range(400)]) == (10.0, 389.0)


def test_c10_the_years_partition_the_window() -> None:
    """S250-C10 / RPT-OUT-07: each pair in one year; the years chain to the whole.

    2017 is partial because the window starts in it (the pair arriving on its first
    point lies outside); 2018 is whole; 2019 ends in June, partial.
    """
    days = trading_days(date(2017, 1, 3), 252 + 251 + 100)
    closes = spy_closes(days, seed=9)
    arm = synthetic_arm("base-25", closes, drift=0.0002, seed=4)
    whole = performance(arm.points, arm.closes)

    windows = year_windows(arm.points)

    assert [(w.label, w.partial) for w in windows] == [
        ("2017", True),
        ("2018", False),
        ("2019", True),
    ]
    later_sessions: list[date] = []
    for window in windows:
        pairs = list(zip(window.points, window.points[1:], strict=False))
        assert all(later[0].year == int(window.label) for _, later in pairs)
        later_sessions.extend(later[0] for _, later in pairs)
    assert later_sessions == [point[0] for point in arm.points[1:]]
    for key in ("portfolio_return_pct", "exposure_matched_return_pct"):
        chained = math.prod(
            1 + performance(w.points, arm.closes)[key] / 100 for w in windows
        )
        assert chained == pytest.approx(1 + whole[key] / 100, abs=1e-9)
