"""S282: annualised portfolio return, family interval and exposure independence.

Agent: tooling
Role: distinguish R from A with literal metric cases and equal equity paths.
External I/O: none.
"""

from dataclasses import replace

import pytest
from scripts.exit_verdict_score import score_exit_arms
from scripts.exit_verdict_stats import COMPARISONS, annualised_return, family_interval
from scripts.replay_verdict_stats import percentile_interval, seeded
from tests.exit_verdict_fixtures import twelve_arms


def test_a4_r_is_annualised_portfolio_return() -> None:
    """S282-A4 / RPT-OUT-07: annualise the reporter's return over its session count."""
    for portfolio, sessions, want in (
        (10, 252, 10),
        (21, 504, 10),
        (-50, 252, -50),
        (10, 0, 0),
    ):
        metrics = {"portfolio_return_pct": portfolio, "performance_sessions": sessions}
        assert annualised_return(metrics) == pytest.approx(want)


def test_a5_family_interval_uses_five_integer_tails() -> None:
    """S282-A5: five comparisons retain the literal order statistics 50 and 9949."""
    values = list(range(10_000))
    seeded(31).shuffle(values)
    assert COMPARISONS == 5
    assert family_interval(values) == (50, 9949)
    assert family_interval(values, comparisons=1) == percentile_interval(values)


def test_a21_dr_reads_equity_return_not_exposure_excess() -> None:
    """S282-A21 / RPT-OUT-07: equal equity and half exposure give dR = 0, dA != 0."""
    arms = twelve_arms(count=121)
    base = arms["stops-25"]
    arms["trail-25"] = replace(
        base, name="trail-25", points=tuple((d, e, h // 2) for d, e, h in base.points)
    )
    result = score_exit_arms(arms, resamples=40)
    difference = result["differences"]["trail-25"]
    assert result["control"]["passed"]
    assert difference["point"] == 0
    assert difference["interval"] == [0, 0]
    assert difference["excess"]["point"] != 0
    assert difference["excess"]["interval"] != [0, 0]
    assert result["verdict"]["readings"]["trail-25"] == "indistinguishable"
