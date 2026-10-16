"""S282: manifest and folder refusals, stable documents and Appendix P labels.

Agent: tooling
Role: exercise the scorer command on complete synthetic replay folders.
External I/O: local temporary files only.
"""

import json
import shutil
from dataclasses import replace
from datetime import date
from pathlib import Path

import pytest
from scripts import exit_verdict_report as report
from scripts.exit_verdict import MANIFEST, main, score_out_root
from scripts.exit_verdict_load import load_exit_arms, manifest_refusals
from scripts.exit_verdict_score import score_exit_arms
from scripts.replay_arms import ArmSpec, load_manifest
from scripts.replay_exits import ExitPolicy
from tests.exit_verdict_fixtures import write_arms
from tests.replay_arm_folders import edit_record, read_record


def test_a15_wrong_manifest_refuses_in_appendix_order() -> None:
    """S282-A15: wrong cost, override, exits, omission and extra are named in order."""
    manifest = load_manifest(MANIFEST)
    arms = list(manifest.arms[:-1])
    arms[0] = replace(arms[0], slippage_bps=30)
    arms[1] = replace(arms[1], overrides=("ANALYST_RELATIVE_STRENGTH_WEIGHT=1.0",))
    arms[2] = replace(arms[2], exits=ExitPolicy(time_exit_sessions=5))
    arms.append(ArmSpec("extra-10", 10, ()))
    refusals = manifest_refusals(replace(manifest, arms=tuple(arms)))
    assert [item["arm"] for item in refusals] == [
        "stops-25",
        "target-25",
        "time10-25",
        "cool5-10",
        "extra-10",
    ]
    for item, fragment in zip(
        refusals[:3],
        ("30 bps", "ANALYST_RELATIVE_STRENGTH_WEIGHT=1.0", "'time_exit_sessions': 5"),
        strict=True,
    ):
        assert fragment in item["reason"]
        assert "Appendix P 25 bps, no overrides" in item["reason"]
    assert refusals[3]["reason"] == "Appendix P names it; the manifest does not"
    assert refusals[4]["reason"] == "the manifest names it; Appendix P does not"


def test_a16_twelve_folders_write_a_complete_verdict(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """S282-A16: command returns 0 and writes numbers, trips, years and provenance."""
    root = write_arms(tmp_path / "arms", {"target-25": 0.001}, count=121)
    assert main(["score", "--out-root", str(root), "--resamples", "40"]) == 0
    document = json.loads((root / "verdict.json").read_text(encoding="utf-8"))
    page = (root / "verdict.md").read_text(encoding="utf-8")
    title = "# EXP-022 verdict: EXIT WINS (leader: target; target), NOT Appendix P"
    assert page.splitlines()[0] == title
    assert capsys.readouterr().out.strip() == title
    assert document["verdict"]["verdict"] == "EXIT WINS"
    assert not document["appendix_p"]
    assert document["refusals"] == []
    assert len(document["arms"]) == 12
    for heading in (
        "Paired differences from stops-only",
        "Arms",
        "Exits (round trips by the reason that closed them)",
        "Years (dR at 25 bps, pts a year)",
        "Control",
        "Provenance",
    ):
        assert f"## {heading}\n" in page
    assert "| stops-25 | stop | 1 | 0.0 | -10.00 | 2 |" in page
    assert "2017, partial" in page
    assert all(arm["profile"]["trips"] == 2 for arm in document["arms"].values())
    assert document["provenance"]["start"] == "2017-01-03"
    assert set(document["provenance"]["withheld_member_sessions"].values()) == {7}


def test_a17_scoring_twice_writes_identical_bytes(tmp_path: Path) -> None:
    """S282-A17: JSON and Markdown are byte-identical on repeated scoring."""
    root = write_arms(tmp_path / "arms", count=61)
    score_out_root(root, resamples=20)
    first = {
        name: (root / name).read_bytes() for name in ("verdict.json", "verdict.md")
    }
    score_out_root(root, resamples=20)
    assert first == {name: (root / name).read_bytes() for name in first}


@pytest.mark.parametrize("case", ["fills", "dropped", "stops", "arm"])
def test_a18_misfitting_folder_refuses_by_name(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], case: str
) -> None:
    """S282-A18: missing fills, wrong exits or an absent arm exit 2 with reasons."""
    root = write_arms(tmp_path / "arms", count=61)
    arm = "stops-25" if case == "stops" else "target-25"
    folder = root / arm
    if case == "fills":
        (folder / "fills.csv").unlink()
    elif case == "arm":
        shutil.rmtree(folder)
    else:
        record = read_record(folder)
        if case == "dropped":
            del record["exits"]
        else:
            record["exits"] = ExitPolicy(take_profit=True).as_dict()
        edit_record(folder, record)
    assert main(["score", "--out-root", str(root), "--resamples", "10"]) == 2
    document = json.loads((root / "verdict.json").read_text(encoding="utf-8"))
    page = (root / "verdict.md").read_text(encoding="utf-8")
    assert document["verdict"] is None
    assert document["arms"] == {}
    reason = (
        "missing fills.csv"
        if case == "fills"
        else "missing arm.json"
        if case == "arm"
        else "exits is"
    )
    assert len(document["refusals"]) == 1
    item = document["refusals"][0]
    assert item["arm"] == arm
    assert reason in item["reason"]
    assert page.startswith("# EXP-022 verdict: NO VERDICT\n")
    assert f"- **{arm}**: {item['reason']}" in page
    assert f"refused: {arm}: {item['reason']}" in capsys.readouterr().out


def test_a19_wrong_manifest_is_never_loaded_and_output_stays_out(
    tmp_path: Path,
) -> None:
    """S282-A19: omitted arm refuses before loading; worktree output raises."""
    manifest = load_manifest(MANIFEST)
    loaded = load_exit_arms(
        tmp_path / "absent", replace(manifest, arms=manifest.arms[:-1])
    )
    assert loaded.refusals == [
        {"arm": "cool5-10", "reason": "Appendix P names it; the manifest does not"}
    ]
    assert loaded.arms == {}
    assert loaded.records == {}
    assert loaded.absent_inputs == {}
    out = Path(__file__).resolve().parents[1] / "s282-no-output"
    with pytest.raises(ValueError, match="inside the worktree"):
        score_out_root(out, resamples=10)
    assert not out.exists()


def test_a20_only_frozen_manifest_and_bootstrap_are_appendix_p(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """S282-A20: frozen settings lose the suffix; each pilot change retains it."""
    root = write_arms(tmp_path / "arms", count=61)
    monkeypatch.setattr(report, "FROZEN_BOOTSTRAP", (20, 20, 0))
    document = score_out_root(root, resamples=20)
    assert document["appendix_p"] is True
    assert "NOT Appendix P" not in (root / "verdict.md").read_text(encoding="utf-8")
    manifest = load_manifest(MANIFEST)
    loaded = load_exit_arms(root, manifest)
    scored = score_exit_arms(loaded.arms, resamples=20)
    profiles = {name: item["profile"] for name, item in document["arms"].items()}
    for pilot in (
        replace(manifest, experiment="pilot"),
        replace(manifest, start=date(2016, 3, 1)),
        replace(manifest, require_history=False),
    ):
        changed = report.verdict_document(pilot, loaded, scored, profiles)
        assert changed["appendix_p"] is False
        assert "NOT Appendix P" in report.render_markdown(changed)
