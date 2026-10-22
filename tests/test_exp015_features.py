"""S289-A1 through A4: features, their history, forward targets and masks.

Agent: tooling
Role: check feature arithmetic independently on synthetic prices.
External I/O: none.
"""

from __future__ import annotations

import numpy as np
import pytest
from scripts.exp015_features import line_features
from scripts.exp015_spec import LINE_FEATURES
from scripts.exp015_targets import adjustment_masks, forward_returns
from tests.exp015_fixtures import price_walk, weekdays


def test_a1_returns_and_history():
    """S289-A1: literal feature order, returns, high distance and warm-up NaNs."""
    high, low, close, volume, spy = price_walk()
    got = line_features(high, low, close, volume, spy)
    expected = (
        "ret_5",
        "ret_20",
        "ret_60",
        "ret_120",
        "ret_252_21",
        "dist_252_high",
        "vol_20",
        "vol_60",
        "atr_pct",
        "beta_60",
        "resvol_60",
        "volratio_5_60",
        "volratio_20_120",
        "dollar_volume",
        "rs_120",
    )
    assert tuple(got) == LINE_FEATURES == expected
    for lag in (5, 20, 60, 120):
        assert np.isnan(got[f"ret_{lag}"][:lag]).all()
        np.testing.assert_allclose(
            got[f"ret_{lag}"][lag:], close[lag:] / close[:-lag] - 1
        )
    assert np.isnan(got["ret_252_21"][:252]).all()
    assert np.isnan(got["dist_252_high"][:251]).all()
    for d in (252, 270, 299):
        assert got["ret_252_21"][d] == pytest.approx(close[d - 21] / close[d - 252] - 1)
        assert got["dist_252_high"][d] == pytest.approx(
            close[d] / max(high[d - 251 : d + 1]) - 1
        )
        rs = (close[d] / close[d - 120]) / (spy[d] / spy[d - 120]) - 1
        assert got["rs_120"][d] == pytest.approx(rs)


def test_a2_risk_volume_and_beta():
    """S289-A2: log ddof=1, OLS beta, residuals, true range and volume windows."""
    rng = np.random.default_rng(17)
    market = rng.normal(0.0003, 0.005, 299)
    spy = 100 * np.r_[1, np.cumprod(1 + market)]
    close = 80 * np.r_[1, np.cumprod(1 + 2 * market)]
    high, low = close * 1.015, close * 0.987
    volume = np.arange(1, 301, dtype=float)
    got = line_features(high, low, close, volume, spy)
    for name, first in (
        ("vol_20", 20),
        ("vol_60", 60),
        ("beta_60", 60),
        ("resvol_60", 60),
        ("atr_pct", 14),
        ("volratio_5_60", 59),
        ("volratio_20_120", 119),
        ("dollar_volume", 19),
        ("rs_120", 120),
    ):
        assert np.isnan(got[name][:first]).all(), name
        assert np.isfinite(got[name][first]), name
    np.testing.assert_allclose(got["beta_60"][60:], 2, atol=1e-11)
    np.testing.assert_allclose(got["resvol_60"][60:], 0, atol=1e-14)
    for d in (120, 205, 299):
        for window in (20, 60):
            logs = np.log(close[d - window + 1 : d + 1] / close[d - window : d])
            assert got[f"vol_{window}"][d] == pytest.approx(np.std(logs, ddof=1))
        assert got["volratio_5_60"][d] == pytest.approx(
            volume[d - 4 : d + 1].mean() / volume[d - 59 : d + 1].mean()
        )
        assert got["volratio_20_120"][d] == pytest.approx(
            volume[d - 19 : d + 1].mean() / volume[d - 119 : d + 1].mean()
        )
        assert got["dollar_volume"][d] == pytest.approx(
            (close * volume)[d - 19 : d + 1].mean()
        )
        tr = [
            max(
                high[j] - low[j],
                abs(high[j] - close[j - 1]),
                abs(low[j] - close[j - 1]),
            )
            for j in range(d - 13, d + 1)
        ]
        assert got["atr_pct"][d] == pytest.approx(np.mean(tr) / close[d])


def test_a3_no_feature_reads_a_later_bar():
    """S289-A3: tripling every future input cannot alter a current or past feature."""
    original = price_walk()
    before = line_features(*original)
    for d in (59, 120, 252, 280):
        changed = [a.copy() for a in original]
        for array in changed:
            array[d + 1 :] *= 3
        after = line_features(*changed)
        for name in before:
            np.testing.assert_allclose(
                before[name][: d + 1], after[name][: d + 1], equal_nan=True
            )


def test_a4_forward_returns_and_adjustment_masks():
    """S289-A4: next-open targets, calendar endpoints, holes and move boundaries."""
    sessions = weekdays(40)
    index = {day: j for j, day in enumerate(sessions)}
    dates = tuple(day for j, day in enumerate(sessions) if j != 11)
    opens = np.array([70 + index[d] for d in dates], dtype=float)
    closes = opens + 3
    got = forward_returns(dates, opens, closes, index, sessions)
    pos = {d: i for i, d in enumerate(dates)}
    for i, day in enumerate(dates):
        j = index[day]
        for k, horizon in enumerate((5, 10, 20)):
            if j + horizon >= 40 or j + 1 == 11 or j + horizon == 11:
                assert np.isnan(got[i, k])
            else:
                assert got[i, k] == pytest.approx(
                    closes[pos[sessions[j + horizon]]] / opens[pos[sessions[j + 1]]] - 1
                )
    feature_mask, target_mask = adjustment_masks(sessions, (sessions[20],), index)
    np.testing.assert_array_equal(feature_mask, np.arange(40) >= 20)
    np.testing.assert_array_equal(target_mask, np.arange(40) < 20)
    long = weekdays(300)
    features, targets = adjustment_masks(
        long, (long[20],), {d: i for i, d in enumerate(long)}
    )
    assert features[20]
    assert features[272]
    assert not features[273]
    assert targets[0]
    assert targets[19]
    assert not targets[20]
