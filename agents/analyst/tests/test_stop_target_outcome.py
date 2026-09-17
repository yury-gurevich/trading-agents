"""Realized-drawdown measurement tests (pure window math).

Agent: analyst
Role: prove a settled window reports its deepest fall and an unsettled one stays absent.
External I/O: none.
"""

from __future__ import annotations

from datetime import date, timedelta

from agents.analyst.domain.stop_target_outcome import (
    observed_drawdown,
    trailing_favorable_excursion,
)
from contracts.provider import OHLCVBar

_DECISION = date(2026, 3, 2)


def test_settled_window_reports_the_deepest_fall_and_the_horizon_it_covers() -> None:
    """ANLZ-OBS-05: the drawdown is close-to-low over the settled window."""
    bars = (*_flat("AAA", days=1, close=100.0), *_lows("AAA", (98.0, 91.0, 95.0)))

    observation = observed_drawdown(bars, _DECISION, 3)

    assert observation is not None
    assert observation.drawdown_pct == 0.09
    assert observation.horizon_days == 3


def test_an_unsettled_window_stays_absent_rather_than_reporting_zero() -> None:
    """ANLZ-OBS-05: too few sessions after the decision is None, never 0.0."""
    bars = (*_flat("AAA", days=1, close=100.0), *_lows("AAA", (98.0, 97.0)))

    assert observed_drawdown(bars, _DECISION, 3) is None


def test_a_name_that_only_rose_records_a_real_zero() -> None:
    """ANLZ-OBS-05: zero drawdown is a measurement, and is distinguishable from None."""
    bars = (*_flat("AAA", days=1, close=100.0), *_lows("AAA", (101.0, 104.0, 110.0)))

    observation = observed_drawdown(bars, _DECISION, 3)

    assert observation is not None
    assert observation.drawdown_pct == 0.0


def test_no_bar_on_or_before_the_decision_day_is_unmeasurable() -> None:
    """ANLZ-OBS-05: without an anchor close there is no denominator."""
    bars = _lows("AAA", (98.0, 97.0, 96.0))

    assert observed_drawdown(bars, _DECISION - timedelta(days=10), 3) is None


def test_a_horizon_below_one_session_measures_nothing() -> None:
    """ANLZ-OBS-05: a zero-length window cannot settle."""
    bars = (*_flat("AAA", days=1, close=100.0), *_lows("AAA", (90.0,)))

    assert observed_drawdown(bars, _DECISION, 0) is None


def test_the_anchor_is_the_last_session_on_or_before_the_decision_day() -> None:
    """ANLZ-OBS-05: a decision on a non-trading day anchors to the prior close."""
    bars = (*_flat("AAA", days=1, close=100.0), *_lows("AAA", (90.0, 95.0)))

    observation = observed_drawdown(bars, _DECISION + timedelta(days=0), 2)

    assert observation is not None
    assert observation.drawdown_pct == 0.10


def test_trailing_favorable_estimate_uses_only_prior_settled_windows() -> None:
    """ANLZ-OBS-06: target estimate uses bars at or before the decision day."""
    bars = tuple(
        _bar(
            "AAA",
            _DECISION - timedelta(days=14 - offset),
            100.0,
            95.0,
            high=130.0 if offset > 4 else 100.0,
        )
        for offset in range(15)
    )
    future_spike = (
        *bars,
        _bar("AAA", _DECISION + timedelta(days=20), 100.0, 95.0, high=500.0),
    )

    observation = trailing_favorable_excursion(future_spike, _DECISION, 10, 120)

    assert observation is not None
    assert observation.excursion_pct == 0.30
    assert observation.horizon_days == 10
    assert observation.sample_count == 5


def test_trailing_favorable_estimate_is_absent_until_one_window_settles() -> None:
    """ANLZ-OBS-06: insufficient prior bars are absence, not measured zero."""
    bars = tuple(
        _bar("AAA", _DECISION - timedelta(days=9 - offset), 100.0, 95.0)
        for offset in range(10)
    )

    assert trailing_favorable_excursion(bars, _DECISION, 10, 120) is None


def test_trailing_favorable_estimate_rejects_zero_horizon() -> None:
    """ANLZ-OBS-06: a zero target horizon cannot produce target evidence."""
    bars = tuple(
        _bar("AAA", _DECISION - timedelta(days=offset), 100.0, 95.0)
        for offset in range(3)
    )

    assert trailing_favorable_excursion(bars, _DECISION, 0, 120) is None


def test_trailing_favorable_estimate_requires_an_anchor_bar() -> None:
    """ANLZ-OBS-06: without a decision-time close there is no target denominator."""
    bars = tuple(
        _bar("AAA", _DECISION + timedelta(days=offset + 1), 100.0, 95.0)
        for offset in range(3)
    )

    assert trailing_favorable_excursion(bars, _DECISION, 1, 120) is None


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


def _bar(
    ticker: str, day: date, close: float, low: float, *, high: float | None = None
) -> OHLCVBar:
    return OHLCVBar(
        ticker=ticker,
        bar_date=day,
        open=close,
        high=max(close, low) + 1.0 if high is None else high,
        low=low,
        close=close,
        volume=1_000_000,
    )
