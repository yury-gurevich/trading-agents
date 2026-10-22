"""S289-A13 through A17: portfolios, bootstrap, the bars and the control.

Agent: tooling
Role: prove literal measurement thresholds and turnover arithmetic.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest
from scripts.exp015_evaluate import decile_spread, top_decile
from scripts.exp015_rule import holdout_reading, interval, verdict, walk_forward_reading
from scripts.exp015_store import shuffled
from scripts.replay_verdict_stats import percentile_interval, seeded, stationary_draws
from tests.exp015_fixtures import fold_record, planted_panel, weekdays


def test_a13_decile_spread():
    """S289-A13: top tenth minus bottom tenth; sessions of nine excluded."""
    prediction = np.r_[np.arange(20), np.arange(9)]
    target = np.r_[np.arange(20) / 100, np.arange(9) * 100]
    days = np.repeat(["large", "small"], [20, 9])
    assert decile_spread(prediction, target, days) == pytest.approx(0.18)
    assert np.isnan(decile_spread(prediction[20:], target[20:], days[20:]))


def test_a14_net_top_decile():
    """S289-A14: hold the top name; charge initial weight, zero on hold, two on swap."""
    days = np.repeat(["d1", "d2"], 10)
    lines = np.tile([f"L{i}" for i in range(10)], 2)
    prediction = np.tile(np.arange(10, dtype=float), 2)
    raw = np.tile(np.linspace(-0.09, 0.09, 10), 2)
    raw[19] = 0.03
    held = top_decile(prediction, raw, days, lines, ("d1", "d2"))
    assert held == pytest.approx(
        {
            "periods": 2,
            "gross_return": 1.09 * 1.03 - 1,
            "net_return": (1.09 - 0.0025) * 1.03 - 1,
        }
    )
    prediction[18] = 20
    raw[18] = 0.12
    swap = top_decile(prediction, raw, days, lines, ("d1", "d2"))
    assert swap["gross_return"] == pytest.approx(1.09 * 1.12 - 1)
    assert swap["net_return"] == pytest.approx((1.09 - 0.0025) * (1.12 - 0.005) - 1)


def test_a15_bootstrap_every_tenth_session():
    """S289-A15: exact S250 interval on every tenth difference, seed zero."""
    values = np.random.default_rng(41).normal(size=300)
    diffs = dict(
        zip((d.isoformat() for d in weekdays(300)), values.tolist(), strict=True)
    )
    sampled = values[::10].tolist()
    rng = seeded(0)
    means = [
        sum(sampled[i] for i in stationary_draws(30, 20, rng)) / 30 for _ in range(200)
    ]
    low, high = percentile_interval(means)
    assert interval(diffs, resamples=200) == pytest.approx(
        {
            "sessions": 30,
            "mean": np.mean(sampled),
            "low": low,
            "high": high,
        }
    )
    assert interval({}) == {"sessions": 0, "mean": None, "low": None, "high": None}


def test_a16_bars_controls_and_verdicts():
    """S289-A16: 0.01 with CI, five wins, failed control and all three bars required."""
    folds = [fold_record(i, 0.03 if i < 5 else -0.01) for i in range(7)]
    control = [fold_record(i, 0.0) for i in range(7)]
    reading = walk_forward_reading(folds, control, resamples=100)
    assert reading["folds_won"] == 5
    assert reading["folds"] == 7
    assert reading["bar1"]
    assert reading["bar2"]
    assert reading["control"]["passed"]
    assert reading["bootstrap"]["low"] > 0
    assert verdict(reading, None) == "PENDING HOLDOUT"
    hold = holdout_reading(fold_record(8, 0.02))
    assert hold["bar3"]
    assert hold["net_ahead"]
    assert verdict(reading, hold) == "PASS"
    failed = fold_record(8, 0.02)
    failed["top_decile"]["ensemble"]["net_return"] = -0.1
    assert not holdout_reading(failed)["bar3"]
    assert not holdout_reading(fold_record(8, 0.0))["bar3"]
    assert verdict(reading, {"bar3": False}) == "FAIL"
    weak = walk_forward_reading(
        [fold_record(i, 0.005) for i in range(7)], control, resamples=50
    )
    assert weak["bootstrap"]["low"] > 0
    assert not weak["bar1"]
    exact = walk_forward_reading(
        [fold_record(i, 0.01) for i in range(7)], control, resamples=50
    )
    assert exact["bar1"]
    leaking = walk_forward_reading(
        folds, [fold_record(i, 0.2) for i in range(7)], resamples=50
    )
    assert not leaking["control"]["passed"]
    assert verdict(leaking, None) == "STOPPED"
    assert verdict(leaking, {"bar3": True}) == "STOPPED"


def test_a17_control_shuffles_only_within_session():
    """S289-A17: reproducible session-local shuffle; other fields unchanged."""
    base = planted_panel(weekdays(5), names=12)
    unique = np.arange(60, dtype=float)
    panel = replace(
        base,
        returns=np.column_stack((unique, unique + 100, unique + 200)),
        spy=np.column_stack((unique + 1, unique + 2, unique + 3)),
    )
    got, again = shuffled(panel, 0), shuffled(panel, 0)
    for name in (
        "sessions",
        "lines",
        "sectors",
        "features",
        "baseline",
        "primary",
        "secondary",
    ):
        np.testing.assert_array_equal(getattr(got, name), getattr(panel, name))
    np.testing.assert_array_equal(got.returns, again.returns)
    assert not np.array_equal(got.returns, panel.returns)
    for day in np.unique(panel.sessions):
        mask = panel.sessions == day
        np.testing.assert_array_equal(
            np.sort(got.returns[mask, 0]), panel.returns[mask, 0]
        )
    np.testing.assert_array_equal(got.spy[:, 0], got.returns[:, 0] + 1)
