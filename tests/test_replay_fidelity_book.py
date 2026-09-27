"""S237 the book the live stages read: held values, held positions and held stops.

Agent: tooling
Role: prove the PM replays on the book live read, and held stops are named, not guessed.
External I/O: local tmp files and a local git binary only.
"""

from __future__ import annotations

import dataclasses
import json
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from scripts.replay_fidelity_inputs import load_session
from scripts.replay_fidelity_stages import replay_pm
from scripts.replay_settings import build_effective_settings
from tests.fidelity_fleet import FleetDay, fleet_graph
from tests.fidelity_fleet_data import HELD_ONLY, SESSIONS
from tests.fidelity_harness import differences, export, replay, rows, tiny_repo

from agents.portfolio_manager.graph_portfolio import portfolio_from_graph

if TYPE_CHECKING:
    from pathlib import Path

SETTINGS = build_effective_settings(())


def _payload(export_dir: Path, run_id: str) -> dict[str, Any]:
    text = (export_dir / f"{run_id}.json").read_text(encoding="utf-8")
    return dict(json.loads(text))


def test_a3_the_books_market_values_reach_the_pm(tmp_path: Path) -> None:
    """PM-NEV-06 / PM-NEV-08: a sector cap filled by held value decides as live did."""
    repo, sha = tiny_repo(tmp_path / "repo")
    run_id = f"sched-{SESSIONS[0].isoformat()}"
    graph = fleet_graph((FleetDay(SESSIONS[0]),), git_sha=sha)
    export_dir = export(graph, tmp_path / "export")
    capped = [
        item["ticker"]
        for item in _payload(export_dir, run_id)["pm"]["rejections"]
        if item["reason"] == "sector_concentration"
    ]
    assert capped

    replay(export_dir, tmp_path / "out", repo)

    reasons = {
        row["ticker"]: row
        for row in rows(tmp_path / "out")
        if row["stage"] == "pm" and row["field"] == "reason"
    }
    assert all(reasons[ticker]["replay"] == "sector_concentration" for ticker in capped)
    assert all(reasons[ticker]["match"] == "True" for ticker in capped)
    inputs = load_session(export_dir / f"{run_id}.json")
    assert inputs.portfolio.position_values
    no_values = dataclasses.replace(
        inputs, portfolio=inputs.portfolio.model_copy(update={"position_values": {}})
    )
    without = replay_pm(no_values, SETTINGS)
    assert without is not None
    assert {intent.ticker for intent in without.approved} & set(capped)


def test_drift_079_the_pm_weighs_a_held_name_at_its_adoption_mark(
    tmp_path: Path,
) -> None:
    """PM-IDN-01 / PM-NEV-06: live reads the adoption-day mark; so does the replay."""
    _repo, sha = tiny_repo(tmp_path / "repo")
    later = f"sched-{SESSIONS[3].isoformat()}"
    graph = fleet_graph((FleetDay(SESSIONS[0]), FleetDay(SESSIONS[3])), git_sha=sha)
    live = portfolio_from_graph(graph, Decimal("100000"), run_id=later)
    export_dir = export(graph, tmp_path / "export")
    snapshot_marks = {
        item["ticker"]: Decimal(item["market_value_cents"]) / 100
        for item in _payload(export_dir, later)["book"]["props"]["holdings"]
    }

    inputs = load_session(export_dir / f"{later}.json")

    assert {k: v.amount for k, v in live.position_values.items()} != snapshot_marks
    assert inputs.portfolio.position_values == live.position_values
    assert inputs.portfolio.cash == live.cash
    assert {position.ticker for position in inputs.held} == set(snapshot_marks)


def test_a_held_stop_exit_is_attributed_to_the_unpersisted_held_stops(
    tmp_path: Path,
) -> None:
    """ANLZ-IDM-01 / DRIFT-074: a live stop exit needs thresholds no export carries."""
    repo, sha = tiny_repo(tmp_path / "repo")
    run_id = f"sched-{SESSIONS[0].isoformat()}"
    underwater = (("T03", 2_000, 2_600), (HELD_ONLY, 1_000, 30_000))
    graph = fleet_graph((FleetDay(SESSIONS[0], holdings=underwater),), git_sha=sha)
    export_dir = export(graph, tmp_path / "export")
    payload = _payload(export_dir, run_id)
    live = {
        item["ticker"]: item
        for item in payload["analyst"]["recommendation_set"]["recommendations"]
    }
    assert (live[HELD_ONLY]["action"], live[HELD_ONLY]["exit_trigger"]) == (
        "sell",
        "stop",
    )
    assert {"held_stops", "active_broker_stop_refs"} <= set(payload["not_persisted"])

    replay(export_dir, tmp_path / "out", repo)

    diffs = differences(tmp_path / "out")
    assert {(row["stage"], row["ticker"]) for row in diffs} == {("analyst", HELD_ONLY)}
    assert {row["field"] for row in diffs} <= {"action", "exit_trigger"}
    assert {row["cause"] for row in diffs} == {"not_persisted:held_stops"}


def test_an_account_the_broker_did_not_answer_is_replayed_as_live_read_it(
    tmp_path: Path,
) -> None:
    """PM-NEV-04 / PM-OUT-03: a stale account rejects buys in the replay as live."""
    repo, sha = tiny_repo(tmp_path / "repo")
    graph = fleet_graph((FleetDay(SESSIONS[0], fresh_account=False),), git_sha=sha)
    export_dir = export(graph, tmp_path / "export")
    reasons = {
        item["reason"]
        for item in _payload(export_dir, f"sched-{SESSIONS[0].isoformat()}")["pm"][
            "rejections"
        ]
    }
    assert "account_unavailable" in reasons

    summary = replay(export_dir, tmp_path / "out", repo)

    assert differences(tmp_path / "out") == []
    assert summary["stages"]["pm"]["agreement"] == 1.0
