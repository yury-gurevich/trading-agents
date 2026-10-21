"""Sprint 288 A13-A14: date bootstrap and strict tail membership.

Agent: forecaster
Role: pin numeric intervals, absent intervals and deterministic return scoring.
External I/O: none.
"""

from dataclasses import replace

import pytest


def test_the_bias_interval_resamples_whole_dates() -> None:
    """FORE-OUT-12 / FORE-IDM-05: two dates span +/-0.01; one date has no interval."""
    from agents.forecaster.domain.barrier_return_scores import ReturnCase, return_scores

    cases = [
        ReturnCase("2026-10-21", 0.02, 0.03, -0.05, 0.0),
        ReturnCase("2026-10-22", 0.02, 0.01, -0.05, 0.0),
    ]
    scores = return_scores(cases)
    assert scores["return_bias"] == pytest.approx(0.0)
    assert scores["return_bias_lo"] == pytest.approx(-0.01)
    assert scores["return_bias_hi"] == pytest.approx(0.01)
    assert return_scores(cases) == scores
    one_date = return_scores([replace(c, as_of="2026-10-21") for c in cases])
    assert "return_bias_lo" not in one_date
    assert "return_bias_hi" not in one_date
    assert one_date["return_bias"] == pytest.approx(0.0)
    assert return_scores([]) == {}


def test_the_tail_share_counts_closes_strictly_below_their_percentile() -> None:
    """FORE-OUT-12: -0.05 equals the tail; only -0.0501 is below it, one of three."""
    from agents.forecaster.domain.barrier_return_scores import ReturnCase, return_scores

    cases = [
        ReturnCase("2026-10-21", 0.0, 0.0, -0.05, close)
        for close in (-0.05, -0.0501, 0.02)
    ]
    assert return_scores(cases)["close_below_p05"] == pytest.approx(1 / 3)
