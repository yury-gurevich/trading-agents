"""Relative-strength signal tests.

Agent: analyst
Role: verify the trailing-return spread, its bands, and the technical-pillar blend.
External I/O: none.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

import pytest

from agents.analyst.domain.relative_strength import (
    _return_pct,
    compute_relative_strength,
    score_relative_strength,
)
from agents.analyst.domain.scoring import _bounded, _composite, score_candidate
from agents.analyst.provider_client import request_market_data
from agents.analyst.settings import AnalystSettings
from agents.analyst.tests.helpers import bar, candidate, candidate_set
from contracts.common import Window
from kernel import CollectingFaultSink, InProcessBus

if TYPE_CHECKING:
    from contracts.provider import OHLCVBar


def _series(ticker: str, closes: list[float]) -> tuple[OHLCVBar, ...]:
    """Bars oldest-first: ``closes[0]`` is the earliest, ``closes[-1]`` the latest."""
    last = len(closes) - 1
    return tuple(
        bar(ticker, last - offset, close) for offset, close in enumerate(closes)
    )


@pytest.mark.parametrize(
    ("relative_strength", "expected"),
    [(6.0, 80.0), (5.0, 60.0), (0.5, 60.0), (0.0, 40.0), (-5.0, 20.0), (-9.0, 20.0)],
)
def test_score_relative_strength_bands(
    relative_strength: float, expected: float
) -> None:
    assert score_relative_strength(relative_strength) == expected


def test_compute_relative_strength_is_return_spread() -> None:
    stock = _series("AAA", [100.0, 105.0, 108.0, 110.0])  # +10% over window 3
    benchmark = _series("SPY", [100.0, 101.0, 103.0, 104.0])  # +4%
    assert compute_relative_strength(stock, benchmark, 3) == pytest.approx(6.0)


def test_return_pct_is_not_hidden_by_spread_cancellation() -> None:
    """Kills x__return_pct__mutmut_11 and x__return_pct__mutmut_18."""
    assert _return_pct(
        _series("AAA", [100.0, 105.0, 108.0, 110.0]), 3
    ) == pytest.approx(10.0)


def test_short_stock_history_is_none() -> None:
    stock = _series("AAA", [100.0, 110.0])
    benchmark = _series("SPY", [100.0, 101.0, 103.0, 104.0])
    assert compute_relative_strength(stock, benchmark, 3) is None


def test_short_benchmark_history_is_none() -> None:
    stock = _series("AAA", [100.0, 105.0, 108.0, 110.0])
    benchmark = _series("SPY", [100.0, 104.0])
    assert compute_relative_strength(stock, benchmark, 3) is None


def test_relative_strength_blends_into_technical_score() -> None:
    settings = AnalystSettings()
    window = settings.rs_window
    cand_bars = _series("AAPL", [100.0 + offset for offset in range(40)])
    benchmark = _series("SPY", [100.0] * window + [101.0])  # mild +1% benchmark

    without = score_candidate(candidate(), cand_bars, {}, (), (), settings)
    with_rs = score_candidate(candidate(), cand_bars, {}, benchmark, (), settings)

    spread = compute_relative_strength(cand_bars, benchmark, window)
    assert spread is not None
    weight = settings.relative_strength_weight
    blended = (1.0 - weight) * without.technical_score + weight * (
        score_relative_strength(spread) / 100.0
    )
    assert with_rs.technical_score == pytest.approx(min(1.0, max(0.0, blended)))
    assert with_rs.metrics["relative_strength"] == pytest.approx(spread)
    assert with_rs.metrics["rs_score"] == pytest.approx(score_relative_strength(spread))


def test_scoring_helpers_hold_exact_boundaries() -> None:
    """Kills agents.analyst.domain.scoring.x__composite__mutmut_24.

    Also kills agents.analyst.domain.scoring.x__bounded__mutmut_10.
    """
    settings = AnalystSettings(alpha158_pillar_weight=0.10)

    assert [_bounded(v) for v in (-0.001, 0.0, 0.001, 1.0, 1.001)] == [
        0.0,
        0.0,
        0.001,
        1.0,
        1.0,
    ]
    assert _composite(0.20, None, None, None, settings) == 0.20
    assert _composite(0.20, 0.80, None, None, settings) == pytest.approx(
        (0.50 * 0.20 + 0.30 * 0.80) / 0.80
    )
    assert _composite(0.20, 0.80, 1.0, 0.50, settings) == pytest.approx(
        (0.50 * 0.20 + 0.30 * 0.80 + 0.20 * 1.0 + 0.10 * 0.50) / 1.10
    )


def test_market_request_is_none_when_provider_unavailable() -> None:
    # The benchmark now rides the market-data request as a dedicated field; with no
    # provider bound the whole request faults and degrades to None (RS then skips).
    bus = InProcessBus()  # no provider bound — the request faults
    sink = CollectingFaultSink()
    end = datetime.now(tz=UTC).date()
    window = Window(start=end - timedelta(days=10), end=end)

    market = request_market_data(
        bus, sink, candidate_set(candidate("AAA")), window, "SPY"
    )
    assert market is None
    assert sink.faults
