"""S282: literal Appendix P arms, reading boundaries and family precedence.

Agent: tooling
Role: prove the pre-registered exit rule independently of its constants.
External I/O: reads the committed manifest only.
"""

from datetime import date
from pathlib import Path

from scripts.exit_verdict_load import manifest_refusals
from scripts.exit_verdict_rule import decide, expected_arms, reading
from scripts.replay_arms import load_manifest
from tests.exit_verdict_fixtures import ARM_NAMES


def test_a1_committed_manifest_is_appendix_p() -> None:
    """S282-A1: twelve ordered arms, frozen metadata and exact exit policies."""
    manifest = load_manifest(
        Path(__file__).resolve().parents[1] / "scripts/exp022_arms.json"
    )
    assert tuple(spec.name for spec in manifest.arms) == ARM_NAMES == expected_arms()
    assert len(manifest.arms) == 12
    assert manifest_refusals(manifest) == []
    assert (manifest.experiment, manifest.start, manifest.require_history) == (
        "EXP-022",
        date(2017, 1, 3),
        True,
    )
    specs = {spec.name: spec for spec in manifest.arms}
    assert specs["target-time10-25"].exits.as_dict() == {
        "take_profit": True,
        "time_exit_sessions": 10,
        "trailing_stop": False,
        "reentry_cooldown_sessions": 0,
    }
    for bps in (25, 10):
        assert not specs[f"stops-{bps}"].exits.declared
        assert specs[f"cool5-{bps}"].exits.reentry_cooldown_sessions == 5
        assert all(
            spec.slippage_bps == bps and not spec.overrides
            for spec in manifest.arms
            if spec.name.endswith(f"-{bps}")
        )


def test_a2_reading_obeys_strict_bounds_and_both_halves() -> None:
    """S282-A2: zero bounds and a nonpositive half never establish a win."""
    cases = (
        ((0.1, 2), (1, 1), "wins"),
        ((0.1, 2), (1, -0.5), "split"),
        ((0.1, 2), (0, 1), "split"),
        ((0, 2), (1, 1), "indistinguishable"),
        ((-2, -0.1), (-1, -1), "behind"),
        ((-2, 0), (-1, -1), "indistinguishable"),
    )
    for interval, halves, want in cases:
        assert reading({"interval": interval, "halves": halves}) == want


def test_a3_bar_family_largest_leader_and_first_tie() -> None:
    """S282-A3: 25 bps precedes 10; largest winning point, first challenger on ties."""
    differences = {
        name: {"point": 0, "interval": [-1, 1], "halves": [0, 0]}
        for name in ARM_NAMES
        if not name.startswith("stops-")
    }
    for name in ("target-25", "time10-25", "cool5-10"):
        differences[name] = {"point": 2, "interval": [1, 3], "halves": [1, 1]}
    result = decide(differences)
    assert (result["verdict"], result["leader"], result["winners"]) == (
        "EXIT WINS",
        "target",
        ["target", "time10"],
    )
    assert len(result["readings"]) == 10
    differences["time10-25"]["point"] = 3
    assert decide(differences)["leader"] == "time10"
    for name in ("target-25", "time10-25"):
        differences[name]["halves"] = [1, 0]
    result = decide(differences)
    assert (result["verdict"], result["leader"]) == ("EXIT WINS AT LOW COST", "cool5")
    differences["cool5-10"]["halves"] = [1, -0.5]
    result = decide(differences)
    assert result["verdict"] == "CHAMPION HOLDS"
    assert result["leader"] is None
    assert result["winners"] == []
    assert result["readings"]["cool5-10"] == "split"
