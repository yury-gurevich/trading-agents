"""S237 clean sessions: only git evidence makes a session clean.

Agent: tooling
Role: prove the deploy SHA is read as live writes it, and every doubt is non-clean.
External I/O: local tmp files and a local git binary only.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, NamedTuple

import pytest
from tests.fidelity_fleet import FleetDay, fleet_graph
from tests.fidelity_fleet_data import SESSIONS
from tests.fidelity_harness import (
    copy_export,
    differences,
    edit_session,
    export,
    replay,
    tiny_repo,
)

if TYPE_CHECKING:
    from pathlib import Path


class Fleet(NamedTuple):
    sha: str
    export: Path


@pytest.fixture(scope="module")
def fleet(tmp_path_factory: pytest.TempPathFactory) -> Fleet:
    """Five fleet runs deployed from a tiny repo's first commit."""
    root = tmp_path_factory.mktemp("fleet")
    _repo, sha = tiny_repo(root / "repo")
    graph = fleet_graph(tuple(FleetDay(day) for day in SESSIONS), git_sha=sha)
    return Fleet(sha, export(graph, root / "export"))


def test_the_export_carries_the_deploy_as_live_writes_it(fleet: Fleet) -> None:
    """ANLZ-OBS-01: the DeployRecord is exported with its live `git_sha` field."""
    payload = json.loads(
        (fleet.export / f"sched-{SESSIONS[0].isoformat()}.json").read_text("utf-8")
    )
    assert payload["deploy"]["git_sha"] == fleet.sha
    assert payload["deploy"]["tag"] == "s-fixture"
    assert "sha" not in payload["deploy"]


def test_a5_code_changed_needs_git_evidence(fleet: Fleet, tmp_path: Path) -> None:
    """ANLZ-IDM-01: a deploy that differs in agents/analyst is non-clean, not pooled."""
    changed = "agents/analyst/domain/analyze.py"
    repo, sha = tiny_repo(tmp_path / "repo", changed=(changed,))
    assert sha == fleet.sha
    export_dir = copy_export(fleet.export, tmp_path / "export")
    edit_session(export_dir, SESSIONS[1], _move_a_hold_confidence)

    summary = replay(export_dir, tmp_path / "out", repo)

    assert {row["cause"] for row in differences(tmp_path / "out")} == {
        f"code_changed:{changed}"
    }
    assert summary["sessions"]["clean"] == []
    assert [item["session"] for item in summary["sessions"]["non_clean"]] == [
        day.isoformat() for day in SESSIONS
    ]
    assert summary["sessions"]["non_clean"][1]["changed"] == [changed]
    assert summary["stages"]["analyst"]["units"] == 0
    assert summary["verdict"] == "INSUFFICIENT"


def test_a_tunables_change_marks_every_session_non_clean(
    fleet: Fleet, tmp_path: Path
) -> None:
    """PM-IDM-01: the pack's tunables are decision code, at their full path."""
    changed = "orchestration/packs/trading_tunables.json"
    repo, _sha = tiny_repo(tmp_path / "repo", changed=(changed,))

    summary = replay(fleet.export, tmp_path / "out", repo)

    assert summary["sessions"]["clean"] == []
    assert {tuple(item["changed"]) for item in summary["sessions"]["non_clean"]} == {
        (changed,)
    }


def test_a_change_outside_the_decision_paths_stays_clean(
    fleet: Fleet, tmp_path: Path
) -> None:
    """SCAN-IDM-01: only decision paths make a session non-clean."""
    repo, _sha = tiny_repo(tmp_path / "repo", changed=("docs/notes.md",))

    summary = replay(fleet.export, tmp_path / "out", repo)

    assert summary["sessions"]["clean"] == [day.isoformat() for day in SESSIONS]
    assert summary["verdict"] == "PASS"


@pytest.mark.parametrize(
    "deploy",
    [None, {}, {"git_sha": ""}, {"git_sha": "0" * 40, "tag": "s-lost"}],
    ids=["no-deploy-key", "no-deploy", "blank-sha", "unresolvable-sha"],
)
def test_an_unknown_deploy_is_never_clean(
    fleet: Fleet, tmp_path: Path, deploy: dict[str, Any] | None
) -> None:
    """ANLZ-IDM-01: a session whose code cannot be proven is code_changed:unknown."""
    repo, _sha = tiny_repo(tmp_path / "repo")
    export_dir = copy_export(fleet.export, tmp_path / "export")
    for day in SESSIONS:
        edit_session(export_dir, day, lambda payload: _set_deploy(payload, deploy))
    edit_session(export_dir, SESSIONS[0], _move_a_hold_confidence)

    summary = replay(export_dir, tmp_path / "out", repo)

    assert summary["sessions"]["clean"] == []
    assert {tuple(item["changed"]) for item in summary["sessions"]["non_clean"]} == {
        ("unknown_deploy",)
    }
    assert {row["cause"] for row in differences(tmp_path / "out")} == {
        "code_changed:unknown_deploy"
    }
    assert summary["verdict"] == "INSUFFICIENT"


def _move_a_hold_confidence(payload: dict[str, Any]) -> None:
    recommendations = payload["analyst"]["recommendation_set"]["recommendations"]
    hold = next(item for item in recommendations if item["action"] == "hold")
    hold["confidence"] = round(hold["confidence"] + 0.01, 12)


def _set_deploy(payload: dict[str, Any], deploy: dict[str, Any] | None) -> None:
    if deploy is None:
        del payload["deploy"]
    else:
        payload["deploy"] = deploy
