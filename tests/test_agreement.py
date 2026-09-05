"""Agreement-proportion tests.

Agent: tooling
Role: prove a rate can never be printed without its denominator or its interval.
External I/O: none.
"""

from __future__ import annotations

from orchestration.agreement import Agreement, wilson_interval


def test_a_rate_is_never_printed_without_what_it_was_taken_over() -> None:
    """A bare percentage is the failure mode this whole sprint exists to fix."""
    detail = Agreement("self_agreement", matched=9, compared=16, excluded=4).detail()

    assert "matched=9" in detail
    assert "compared=16" in detail
    assert "excluded=4" in detail
    assert "rate=56.25%" in detail
    assert "ci95=[" in detail


def test_nothing_compared_reports_n_a_rather_than_zero_percent() -> None:
    """0% and "we compared nothing" are different claims about the world."""
    empty = Agreement("self_agreement", matched=0, compared=0, excluded=7)

    assert empty.rate is None
    assert empty.interval is None
    assert "rate=n/a (nothing was compared)" in empty.detail()


def test_a_missing_counterpart_is_not_counted_as_an_exclusion() -> None:
    """A shrinking overlap must not read as a rising fail-open rate."""
    detail = Agreement(
        "cross", matched=3, compared=4, excluded=1, no_counterpart=9
    ).detail()

    assert "excluded=1" in detail
    assert "no_counterpart=9" in detail


def test_the_interval_is_wilsons_by_value_not_merely_by_range() -> None:
    """DL-104's 9 of 16, to four places. A range assertion passed a broken
    denominator in the 2026-09-05 mutation sweep; only pinned values catch it."""
    low, high = wilson_interval(9, 16) or (0.0, 0.0)

    assert round(low, 4) == 0.3318
    assert round(high, 4) == 0.7690


def test_the_interval_stays_inside_zero_and_one_at_the_extremes() -> None:
    """The normal approximation leaves [0,1] here; Wilson is chosen for this."""
    low, high = wilson_interval(4, 4) or (0.0, 0.0)

    assert 0.0 <= low <= high <= 1.0
    assert round(high, 6) == 1.0
    assert round(low, 4) == 0.5101


def test_a_small_sample_gets_a_wide_interval_and_a_large_one_a_narrow_one() -> None:
    """The interval is what stops a 3-of-4 being quoted as 75% and believed."""
    small = wilson_interval(3, 4) or (0.0, 1.0)
    large = wilson_interval(300, 400) or (0.0, 1.0)

    assert (small[1] - small[0]) > (large[1] - large[0])


def test_no_interval_exists_when_nothing_was_compared() -> None:
    """An interval over an empty sample would be an invented number."""
    assert wilson_interval(0, 0) is None
