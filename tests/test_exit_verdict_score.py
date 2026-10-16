"""S282: shared bootstrap draws, cost pairing, controls and window refusals.

Agent: tooling
Role: prove planted gain, loss and split paths through real reporter statistics.
External I/O: none.
"""

from dataclasses import replace

import pytest
from scripts import exit_verdict_score as scorer
from scripts.exit_verdict_stats import R_KEY
from tests.exit_verdict_fixtures import twelve_arms


def test_a6_gain_wins_and_family_copy_is_exactly_zero() -> None:
    """S282-A6 / RPT-OUT-07: paired shared draws cancel a copy at its own cost."""
    result = scorer.score_exit_arms(twelve_arms({"target-25": 0.001}), resamples=80)
    difference = result["differences"]["target-25"]
    assert difference["interval"][0] > 10
    assert all(value > 0 for value in difference["halves"])
    assert difference["point"] == (
        result["arms"]["target-25"]["whole"][R_KEY]
        - result["arms"]["stops-25"]["whole"][R_KEY]
    )
    copy = result["differences"]["trail-10"]
    assert (copy["champion"], copy["point"], copy["interval"]) == (
        "stops-10",
        0,
        [0, 0],
    )
    assert result["bootstrap"] == {
        "comparisons": 5,
        "mean_block": 20,
        "pairs": 300,
        "resamples": 80,
        "seed": 0,
    }
    assert result["verdict"]["verdict"] == "EXIT WINS"
    assert result["verdict"]["leader"] == "target"


def test_a7_loss_is_behind_and_champion_holds() -> None:
    """S282-A7: a planted daily loss is behind in return and excess."""
    result = scorer.score_exit_arms(twelve_arms({"time10-25": -0.001}), resamples=60)
    difference = result["differences"]["time10-25"]
    assert difference["interval"][1] < -10
    assert difference["excess"]["point"] < -10
    assert result["verdict"]["readings"]["time10-25"] == "behind"
    assert result["verdict"]["verdict"] == "CHAMPION HOLDS"


def test_a8_whole_gain_with_losing_half_is_split() -> None:
    """S282-A8: half windows share the midpoint and cannot be replaced by years."""
    result = scorer.score_exit_arms(
        twelve_arms({"trail-25": (0.003, -0.0005)}), resamples=80
    )
    difference = result["differences"]["trail-25"]
    assert difference["interval"][0] > 0
    assert difference["halves"][0] > 0 > difference["halves"][1]
    halves = result["arms"]["trail-25"]["halves"]
    assert [row["label"] for row in halves] == ["first half", "second half"]
    assert halves[0]["last"] == halves[1]["first"]
    assert result["verdict"]["readings"]["trail-25"] == "split"


def test_a9_only_low_cost_gain_wins_at_low_cost() -> None:
    """S282-A9: a 10 bps win never promotes its 25 bps counterpart."""
    result = scorer.score_exit_arms(twelve_arms({"cool5-10": 0.001}), resamples=60)
    assert result["verdict"]["verdict"] == "EXIT WINS AT LOW COST"
    assert result["verdict"]["leader"] == "cool5"
    assert result["verdict"]["readings"]["cool5-25"] == "indistinguishable"


def test_a10_control_checks_both_r_and_a_and_refuses(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """S282-A10 / RPT-OUT-07: negative tolerance or wrong rebuilt exposure refuses."""
    arms = twelve_arms(count=61)
    passed = scorer.score_exit_arms(arms, resamples=10)
    assert passed["control"]["passed"]
    assert passed["control"]["max_deviation_pts"] <= 1e-6
    with monkeypatch.context() as patch:
        patch.setattr(scorer, "CONTROL_TOLERANCE_PTS", -1)
        refused = scorer.score_exit_arms(arms, resamples=10)
    assert not refused["control"]["passed"]
    assert refused["refusals"][0]["arm"] == "control"
    assert "within -1" in refused["refusals"][0]["reason"]
    assert refused["verdict"] is None
    assert refused["differences"] == {}
    original = scorer.resampled

    def half_exposure(pairs, order):
        return original([(a, b, held // 2, c, d) for a, b, held, c, d in pairs], order)

    monkeypatch.setattr(scorer, "resampled", half_exposure)
    refused = scorer.score_exit_arms(arms, resamples=10)
    assert not refused["control"]["passed"]
    assert refused["control"]["max_deviation_pts"] > 1e-6
    assert refused["refusals"][0]["arm"] == "control"
    assert refused["verdict"] is None
    assert refused["differences"] == {}


def test_a11_gap_and_unequal_pairs_refuse() -> None:
    """S282-A11: missing interior SPY close means two gaps; short pairs raise."""
    arms = twelve_arms(count=61)
    base = arms["target-25"]
    closes = dict(base.closes)
    del closes[base.points[20][0]]
    arms[base.name] = replace(base, closes=closes)
    refused = scorer.score_exit_arms(arms, resamples=10)
    assert refused["refusals"] == [
        {"arm": "target-25", "reason": "2 gap session(s) in the scored window"}
    ]
    assert refused["control"] is None
    assert refused["verdict"] is None
    assert refused["differences"] == {}
    assert refused["bootstrap"] == {}
    arms[base.name] = replace(base, points=base.points[:-1])
    with pytest.raises(
        ValueError, match="arms differ in their number of session pairs"
    ):
        scorer.score_exit_arms(arms, resamples=10)


def test_a12_seed_repeats_draws_and_changes_only_interval() -> None:
    """S282-A12: seeds 3, 3, 4 repeat exactly then move the interval, not the point."""
    arms = twelve_arms({"target-25": 0.001}, count=121)
    first, same, other = [
        scorer.score_exit_arms(arms, resamples=40, seed=s) for s in (3, 3, 4)
    ]
    assert first == same
    a, b = first["differences"]["target-25"], other["differences"]["target-25"]
    assert a["point"] == b["point"]
    assert a["interval"] != b["interval"]
