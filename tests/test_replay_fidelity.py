"""S237 Layer 1: the replay decides what the fleet decided, on the fleet's own inputs.

Agent: tooling
Role: prove each stage is replayed by the fleet's code, located, and never read back.
External I/O: local tmp files and a local git binary only.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, NamedTuple

import pytest
from scripts.replay_fidelity_compare import run_fidelity
from tests.fidelity_fleet import FleetDay, fleet_graph
from tests.fidelity_fleet_data import HIGH_BETA, SESSIONS
from tests.fidelity_harness import (
    copy_export,
    differences,
    edit_session,
    export,
    replay,
    rows,
    tiny_repo,
)

if TYPE_CHECKING:
    from datetime import date

ROOT = Path(__file__).resolve().parents[1]


class Fleet(NamedTuple):
    repo: Path
    export: Path


@pytest.fixture(scope="module")
def fleet(tmp_path_factory: pytest.TempPathFactory) -> Fleet:
    """Five scheduled runs decided by the fleet's own graph-pull stages."""
    root = tmp_path_factory.mktemp("fleet")
    repo, sha = tiny_repo(root / "repo")
    graph = fleet_graph(tuple(FleetDay(day) for day in SESSIONS), git_sha=sha)
    return Fleet(repo, export(graph, root / "export"))


def test_a1_identical_inputs_agree(fleet: Fleet, tmp_path: Path) -> None:
    """SCAN-IDM-01 / ANLZ-IDM-01 / PM-IDM-01: the fleet's inputs give its decisions."""
    summary = replay(fleet.export, tmp_path / "out", fleet.repo)

    assert summary["verdict"] == "PASS"
    assert summary["replayed"] == {"scanner": 5, "analyst": 5, "pm": 5}
    stages = summary["stages"]
    assert {name: stages[name]["agreement"] for name in stages} == {
        "scanner": 1.0,
        "analyst": 1.0,
        "pm": 1.0,
    }
    assert all(stages[name]["causes"] == {} for name in stages)
    assert stages["scanner"]["sessions"] == 5
    assert stages["analyst"]["units"] >= 100
    assert stages["pm"]["units"] >= 10
    assert stages["pm"]["hold_passthrough"] == {"units": 10, "matches": 10}
    assert summary["unexplained"] == 0
    assert differences(tmp_path / "out") == []
    confidences = [
        row
        for row in rows(tmp_path / "out")
        if row["stage"] == "analyst" and row["field"] == "confidence" and row["live"]
    ]
    assert len(confidences) >= 90
    assert all(row["replay"] for row in confidences)


def test_a2_a_changed_live_output_is_caught_and_located(
    fleet: Fleet, tmp_path: Path
) -> None:
    """ANLZ-IDM-01 / PM-IDM-01: one moved confidence is one analyst difference."""
    export_dir = copy_export(fleet.export, tmp_path / "export")
    session = SESSIONS[2]
    moved: list[str] = []

    def move(payload: dict[str, Any]) -> None:
        recommendations = payload["analyst"]["recommendation_set"]["recommendations"]
        hold = next(item for item in recommendations if item["action"] == "hold")
        hold["confidence"] = round(hold["confidence"] + 0.01, 12)
        moved.append(hold["ticker"])

    edit_session(export_dir, session, move)
    summary = replay(export_dir, tmp_path / "out", fleet.repo)

    diffs = differences(tmp_path / "out")
    assert [(r["session"], r["stage"], r["ticker"], r["field"]) for r in diffs] == [
        (session.isoformat(), "analyst", moved[0], "confidence")
    ]
    assert diffs[0]["cause"] == "unexplained"
    assert summary["stages"]["scanner"]["agreement"] == 1.0
    assert summary["stages"]["pm"]["agreement"] == 1.0
    assert summary["stages"]["analyst"]["causes"] == {"unexplained": 1}
    assert summary["verdict"] == "FAIL"


def test_a4_a_benchmark_live_used_but_never_stored_is_named(
    fleet: Fleet, tmp_path: Path
) -> None:
    """SCAN-OUT-06 / SCAN-IDM-01: a missing benchmark is named, never invented."""
    export_dir = copy_export(fleet.export, tmp_path / "export")
    session = SESSIONS[0]

    def unstore(payload: dict[str, Any]) -> None:
        payload["market"]["snapshot"]["benchmark"] = []
        payload["not_persisted"] = sorted({*payload["not_persisted"], "benchmark"})

    edit_session(export_dir, session, unstore)
    replay(export_dir, tmp_path / "out", fleet.repo)

    diffs = [
        row
        for row in differences(tmp_path / "out")
        if row["session"] == session.isoformat()
    ]
    beta_name = next(
        row for row in diffs if row["stage"] == "scanner" and row["ticker"] == HIGH_BETA
    )
    assert beta_name["live"] == ""  # live's beta cap dropped it
    assert beta_name["replay"] != ""  # the replay had no SPY, so the cap never ran
    assert {row["stage"] for row in diffs} == {"scanner", "analyst"}
    assert {row["cause"] for row in diffs} == {"not_persisted:benchmark"}
    other_sessions = [
        row
        for row in differences(tmp_path / "out")
        if row["session"] != session.isoformat()
    ]
    assert other_sessions == []


@pytest.mark.parametrize("key", ["replay", "layer2"])
def test_an_export_carrying_replay_outputs_is_refused(
    fleet: Fleet, tmp_path: Path, key: str
) -> None:
    """SCAN-IDM-01 / ANLZ-IDM-01 / PM-IDM-01: replay outputs are computed, not read."""
    export_dir = copy_export(fleet.export, tmp_path / "export")
    edit_session(export_dir, SESSIONS[1], lambda payload: payload.update({key: {}}))

    with pytest.raises(ValueError, match=key):
        replay(export_dir, tmp_path / "out", fleet.repo)
    assert not (tmp_path / "out" / "summary.json").exists()


def test_a_stage_with_no_replay_is_never_read_as_the_live_output(
    fleet: Fleet, tmp_path: Path
) -> None:
    """SCAN-IDM-01 / ANLZ-IDM-01 / PM-IDM-01: no replay is harness:not_replayed."""
    export_dir = copy_export(fleet.export, tmp_path / "export")
    session = SESSIONS[3]
    edit_session(export_dir, session, _drop_snapshot)

    summary = replay(export_dir, tmp_path / "out", fleet.repo)

    diffs = differences(tmp_path / "out")
    assert {row["session"] for row in diffs} == {session.isoformat()}
    assert {row["stage"] for row in diffs} == {"scanner", "analyst", "pm"}
    assert {row["cause"] for row in diffs} == {"harness:not_replayed"}
    assert all(row["replay"] == "" for row in diffs)
    assert summary["replayed"] == {"scanner": 4, "analyst": 4, "pm": 4}
    assert summary["verdict"] == "FAIL"


def test_a10_fidelity_outputs_refuse_the_worktree(fleet: Fleet) -> None:
    """RPT-NEV-02: fidelity outputs, which hold vendor bars, stay outside the repo."""
    target = ROOT / "fidelity-out"
    with pytest.raises(ValueError, match="inside the worktree"):
        run_fidelity(export=fleet.export, cache=None, out=target, repo=fleet.repo)
    assert not target.exists()


def _drop_snapshot(payload: dict[str, Any]) -> None:
    payload["market"]["snapshot"] = None


def _session_file(export_dir: Path, session: date) -> Path:
    return export_dir / f"sched-{session.isoformat()}.json"
