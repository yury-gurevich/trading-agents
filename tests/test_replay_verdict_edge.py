"""S250: a planted edge is found, a planted null is not, and arms meet on the same days.

Agent: tooling
Role: prove the scorer's verdict, paired differences and control on synthetic arms.
External I/O: none.

The drift and noise are chosen far from the boundary (see the fixtures): over 300
pairs the noise gives an annualised standard error near 2.9 points, and a planted
drift of 0.001 a session is about +28 points a year, near ten standard errors out.
The null's noise is centred, so its point estimate sits on 0 by construction.
"""

from __future__ import annotations

import pytest
from scripts.replay_verdict_score import score_arms
from scripts.replay_verdict_stats import replica_pairs
from tests.replay_verdict_fixtures import EDGE_DRIFT, five_arms, shifted

RESAMPLES = 200  # the command's default is 10,000; the tests keep to a few hundred


def test_c6_a_planted_edge_is_found_and_a_planted_null_is_not() -> None:
    """S250-C6 / RPT-OUT-07: EDGE; NO EDGE indistinguishable; NO EDGE behind."""
    edge = score_arms(five_arms(EDGE_DRIFT, 0.0), resamples=RESAMPLES, seed=0)
    null = score_arms(five_arms(0.0, 0.0), resamples=RESAMPLES, seed=0)
    behind = score_arms(
        five_arms(-EDGE_DRIFT, -EDGE_DRIFT), resamples=RESAMPLES, seed=0
    )

    assert edge["refusals"] == []
    assert edge["verdict"] == {"verdict": "EDGE", "reading": None, "pillars": []}
    assert edge["arms"]["base-25"]["interval"][0] > 10.0
    assert null["verdict"] == {
        "verdict": "NO EDGE",
        "reading": "indistinguishable",
        "pillars": [],
    }
    low, high = null["arms"]["base-25"]["interval"]
    assert low < -1.0 < 1.0 < high
    assert behind["verdict"] == {
        "verdict": "NO EDGE",
        "reading": "behind",
        "pillars": [],
    }
    assert behind["arms"]["base-25"]["interval"][1] < -10.0


def test_c9_arms_are_compared_on_the_same_days() -> None:
    """S250-C9: an ablation equal to base-25 differs by exactly 0; drifted, it wins."""
    arms = five_arms(0.0, 0.0)
    base = arms["base-25"]
    same = {**arms, "technical-only-25": shifted(base, "technical-only-25", 0.0)}
    ahead = {
        **arms,
        "relative-strength-only-25": shifted(
            base, "relative-strength-only-25", EDGE_DRIFT
        ),
    }

    equal = score_arms(same, resamples=RESAMPLES, seed=0)
    better = score_arms(ahead, resamples=RESAMPLES, seed=0)

    assert equal["differences"]["technical-only-25"] == {
        "point": 0.0,
        "interval": [0.0, 0.0],
    }
    assert better["differences"]["relative-strength-only-25"]["interval"][0] > 10.0
    assert better["verdict"] == {
        "verdict": "EDGE IN A PILLAR",
        "reading": None,
        "pillars": ["relative-strength-only-25"],
    }


def test_c13_the_control_scores_zero_and_a_failing_control_refuses() -> None:
    """S250-C13 / RPT-OUT-07: SPY at base-25's exposure scores 0, interval [0, 0]."""
    arms = five_arms(EDGE_DRIFT, 0.0)

    scored = score_arms(arms, resamples=RESAMPLES, seed=0)

    control = scored["control"]
    assert control["passed"] is True
    assert control["annualised_excess_pts"] == pytest.approx(0.0, abs=1e-6)
    assert control["interval"] == pytest.approx([0.0, 0.0], abs=1e-6)

    def leaky(pairs: tuple) -> tuple:
        return tuple(
            (e0, e1 + e0 // 10_000, l0, s0, s1)
            for e0, e1, l0, s0, s1 in replica_pairs(pairs)
        )

    broken = score_arms(arms, resamples=RESAMPLES, seed=0, replica=leaky)

    assert broken["control"]["passed"] is False
    assert broken["verdict"] is None
    assert broken["refusals"] == [
        {
            "arm": "control",
            "reason": broken["refusals"][0]["reason"],
        }
    ]
    assert "replica of base-25" in broken["refusals"][0]["reason"]
