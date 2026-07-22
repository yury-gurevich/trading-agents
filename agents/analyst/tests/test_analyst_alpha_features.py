"""Alpha158 feature computation tests.

Agent: analyst
Role: verify compute_alpha_features returns correct values and degrades cleanly.
External I/O: none.
"""

from __future__ import annotations

import dataclasses
from datetime import UTC, datetime, timedelta

import pytest

from agents.analyst.domain.alpha_features import compute_alpha_features
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


def test_all_fields_match_known_mixed_series_snapshot() -> None:
    """Kills x_compute_alpha_features__mutmut_6/_7/_9/_11/_14/_15/_16."""
    closes = [
        100,
        103,
        101,
        106,
        102,
        109,
        105,
        111,
        107,
        114,
        110,
        117,
        113,
        119,
        115,
        122,
        118,
        124,
        120,
        127,
        123,
        129,
        125,
        132,
        128,
        134,
        130,
        137,
        133,
        139,
        135,
        142,
        138,
        144,
        140,
        147,
        143,
        149,
        145,
        152,
        148,
        154,
        150,
        157,
        153,
        159,
        155,
        162,
        158,
        164,
        160,
        167,
        163,
        169,
        165,
        172,
        168,
        174,
        170,
        177,
        173,
        179,
        175,
        182,
        178,
    ]
    row = compute_alpha_features(_bars([float(close) for close in closes]))
    assert row is not None
    assert dataclasses.astuple(row) == pytest.approx(
        [
            0.005649717514124294,
            0.07878787878787878,
            0.16339869281045752,
            0.7450980392156863,
            0.029270836857948495,
            0.03079405961284074,
            0.03169042214126789,
            0.038846843499095014,
            0.04,
            0.04242424242424243,
            0.04516129032258064,
            0.06862745098039216,
            -0.022598870056497175,
            -0.023255813953488372,
            -0.025157232704402517,
            -0.03669724770642202,
            0.1,
            0.05,
            1.0 / 60.0,
            1.0,
            1.0,
            1.0,
        ],
        abs=1e-12,
    )


def test_std_is_zero_for_flat_prices() -> None:
    flat = _bars([100.0] * 65)
    row = compute_alpha_features(flat)
    assert row is not None
    assert row.std_5 == pytest.approx(0.0)
    assert row.std_60 == pytest.approx(0.0)


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
