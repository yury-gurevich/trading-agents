"""Alpha158 feature computation tests.

Agent: analyst
Role: verify compute_alpha_features returns correct values and degrades cleanly.
External I/O: none.
"""

from __future__ import annotations

import dataclasses
import math
from datetime import UTC, datetime, timedelta

import pytest

from agents.analyst.domain.alpha_features import AlphaFeatureRow, compute_alpha_features
from contracts.provider import OHLCVBar


def _bar(close: float, days_ago: int) -> OHLCVBar:
    day = datetime.now(tz=UTC).date() - timedelta(days=days_ago)
    return OHLCVBar(
        ticker="TEST",
        bar_date=day,
        open=close,
        high=close,
        low=close,
        close=close,
        volume=1000,
    )


def _bars(closes: list[float]) -> tuple[OHLCVBar, ...]:
    """Build bars newest-last from a list of closes ordered oldest-first."""
    n = len(closes)
    return tuple(_bar(c, n - 1 - i) for i, c in enumerate(closes))


def _linear(n: int = 65, start: float = 1.0) -> tuple[OHLCVBar, ...]:
    """Return n bars with closes [start, start+1, ..., start+n-1]."""
    return _bars([float(start + i) for i in range(n)])


def test_returns_none_when_fewer_than_62_bars() -> None:
    assert compute_alpha_features(_linear(61)) is None


def test_returns_row_with_exactly_62_bars() -> None:
    assert compute_alpha_features(_linear(62)) is not None


def test_all_fields_are_finite() -> None:
    row = compute_alpha_features(_linear(65))
    assert row is not None
    for f in dataclasses.fields(AlphaFeatureRow):
        assert math.isfinite(getattr(row, f.name)), f"{f.name} is not finite"


def test_roc_5_matches_manual_calculation() -> None:
    # closes = [1, 2, ..., 65]; roc_5 = (65 - 60) / 60 = 1/12
    row = compute_alpha_features(_linear(65))
    assert row is not None
    assert row.roc_5 == pytest.approx(5.0 / 60.0)


def test_roc_10_matches_manual_calculation() -> None:
    row = compute_alpha_features(_linear(65))
    assert row is not None
    assert row.roc_10 == pytest.approx(10.0 / 55.0)


def test_roc_60_matches_manual_calculation() -> None:
    # closes[-61] = 5, closes[-1] = 65; roc_60 = (65 - 5) / 5 = 12.0
    row = compute_alpha_features(_linear(65))
    assert row is not None
    assert row.roc_60 == pytest.approx(12.0)


def test_std_5_is_non_negative() -> None:
    row = compute_alpha_features(_linear(65))
    assert row is not None
    assert row.std_5 >= 0.0


def test_std_is_zero_for_flat_prices() -> None:
    flat = _bars([100.0] * 65)
    row = compute_alpha_features(flat)
    assert row is not None
    assert row.std_5 == pytest.approx(0.0)
    assert row.std_60 == pytest.approx(0.0)


def test_max_ret_exceeds_min_ret() -> None:
    row = compute_alpha_features(_linear(65))
    assert row is not None
    assert row.max_5 >= row.min_5
    assert row.max_60 >= row.min_60


def test_imax_is_zero_for_monotone_increasing_prices() -> None:
    # Max is always the most recent bar → idx = w → 1.0 - w/w = 0.0
    row = compute_alpha_features(_linear(65))
    assert row is not None
    assert row.imax_10 == pytest.approx(0.0)
    assert row.imax_20 == pytest.approx(0.0)
    assert row.imax_60 == pytest.approx(0.0)


def test_imin_is_one_for_monotone_increasing_prices() -> None:
    # Min is always the oldest bar in the window → idx = 0 → 1.0 - 0/w = 1.0
    row = compute_alpha_features(_linear(65))
    assert row is not None
    assert row.imin_10 == pytest.approx(1.0)
    assert row.imin_20 == pytest.approx(1.0)
    assert row.imin_60 == pytest.approx(1.0)


def test_imax_is_one_for_monotone_decreasing_prices() -> None:
    # Max is always at the oldest position → idx = 0 → 1.0 - 0/w = 1.0
    decreasing = _bars([float(65 - i) for i in range(65)])
    row = compute_alpha_features(decreasing)
    assert row is not None
    assert row.imax_10 == pytest.approx(1.0)


def test_imin_is_zero_for_monotone_decreasing_prices() -> None:
    # Min is always the most recent bar → idx = w → 1.0 - w/w = 0.0
    decreasing = _bars([float(65 - i) for i in range(65)])
    row = compute_alpha_features(decreasing)
    assert row is not None
    assert row.imin_10 == pytest.approx(0.0)
