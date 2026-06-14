"""Golden-value tests for the kernel smoother and calendar signal.

Agent: analyst
Role: pin hand-computed NW deviations and the always-emit turnaround flag.
External I/O: none.
"""

from __future__ import annotations

from datetime import date

import pytest

from agents.analyst.domain import indicators_kernel as ik

# 2025-01-03 is a Friday, 2025-01-06 a Monday, 2025-01-07 a Tuesday.
_FRI, _MON, _TUE = date(2025, 1, 3), date(2025, 1, 6), date(2025, 1, 7)


def test_nadaraya_watson_last_above_line_is_positive() -> None:
    # Flat 10 then a spike up: the last close sits above the smoothed line (+dev).
    closes = [10.0] * 9 + [20.0]
    assert ik.nadaraya_watson(closes, 8.0, 50) == pytest.approx(78.19696566, abs=1e-6)


def test_nadaraya_watson_last_below_line_is_negative() -> None:
    # Flat 20 then a drop: the last close sits below the smoothed line (-dev).
    closes = [20.0] * 9 + [10.0]
    assert ik.nadaraya_watson(closes, 8.0, 50) == pytest.approx(-46.74183689, abs=1e-6)


def test_nadaraya_watson_returns_none_below_ten_closes() -> None:
    assert ik.nadaraya_watson([1.0] * 9, 8.0, 50) is None


def test_nadaraya_watson_returns_none_when_smoothed_is_zero() -> None:
    # An all-zero window smooths to 0.0, which the deviation guard rejects.
    assert ik.nadaraya_watson([0.0] * 12, 8.0, 50) is None


def test_turnaround_true_on_monday_below_prior_friday() -> None:
    closes = [12.0, 11.0, 10.0]  # Monday close below the prior Friday close.
    assert ik.turnaround_signal(closes, [_FRI, date(2025, 1, 4), _MON]) is True


def test_turnaround_false_on_monday_at_or_above_prior_friday() -> None:
    closes = [10.0, 11.0, 12.0]  # Monday close above the prior Friday close.
    assert ik.turnaround_signal(closes, [_FRI, date(2025, 1, 4), _MON]) is False


def test_turnaround_false_on_non_monday_is_emitted_not_skipped() -> None:
    closes = [10.0, 11.0, 12.0]
    assert ik.turnaround_signal(closes, [_FRI, _MON, _TUE]) is False


def test_turnaround_false_on_monday_when_history_breaks_before_friday() -> None:
    # Sat, Sun, Mon: the four-bar walk-back runs out of bars (break) with no Friday.
    closes = [10.0, 11.0, 12.0]
    dates = [date(2025, 1, 4), date(2025, 1, 5), date(2025, 1, 6)]
    assert ik.turnaround_signal(closes, dates) is False


def test_turnaround_false_on_monday_when_lookback_finds_no_friday() -> None:
    # Tue, Wed, Thu, Sun, Mon: the full four-bar walk-back completes with no Friday.
    closes = [10.0, 11.0, 12.0, 13.0, 14.0]
    dates = [
        date(2024, 12, 31),
        date(2025, 1, 1),
        date(2025, 1, 2),
        date(2025, 1, 5),
        date(2025, 1, 6),
    ]
    assert ik.turnaround_signal(closes, dates) is False


def test_turnaround_returns_none_below_three_bars() -> None:
    assert ik.turnaround_signal([10.0, 11.0], [_FRI, _MON]) is None
