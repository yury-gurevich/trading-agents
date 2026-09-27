"""S237 replay edges: a book not rebuilt, a regime not stored, one tolerance, outcomes.

Agent: tooling
Role: prove each named gap reaches its cause, and the smallest rules hold.
External I/O: local tmp files and a local git binary only.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, NamedTuple

import pytest
from scripts.replay_fidelity_layer3 import layer3_row
from scripts.replay_fidelity_layers import TOLERANCE, matches, scanner_rows
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
    repo: Path
    export: Path


@pytest.fixture(scope="module")
def fleet(tmp_path_factory: pytest.TempPathFactory) -> Fleet:
    """One scheduled run decided by the fleet's own stages."""
    root = tmp_path_factory.mktemp("fleet")
    repo, sha = tiny_repo(root / "repo")
    graph = fleet_graph((FleetDay(SESSIONS[0]),), git_sha=sha)
    return Fleet(repo, export(graph, root / "export"))


def test_a_book_the_export_could_not_rebuild_names_held_positions(
    fleet: Fleet, tmp_path: Path
) -> None:
    """PM-IDN-01 / ANLZ-IDM-01: held and PM differences go to the unrebuilt book."""
    export_dir = copy_export(fleet.export, tmp_path / "export")

    def lose(payload: dict[str, Any]) -> None:
        payload["positions"] = []
        payload["not_persisted"] = sorted({*payload["not_persisted"], "held_positions"})

    edit_session(export_dir, SESSIONS[0], lose)
    replay(export_dir, tmp_path / "out", fleet.repo)

    diffs = differences(tmp_path / "out")
    assert {row["stage"] for row in diffs} == {"analyst", "pm"}
    assert {row["cause"] for row in diffs} == {"not_persisted:held_positions"}


def test_a_run_whose_regime_was_not_stored_replays_the_scanner_only(
    fleet: Fleet, tmp_path: Path
) -> None:
    """ANLZ-IDM-01 / PM-IDM-01: no regime, no analyst or PM replay; never live."""
    export_dir = copy_export(fleet.export, tmp_path / "export")
    edit_session(export_dir, SESSIONS[0], lambda payload: payload.update(regime={}))

    summary = replay(export_dir, tmp_path / "out", fleet.repo)

    diffs = differences(tmp_path / "out")
    assert {row["stage"] for row in diffs} == {"analyst", "pm"}
    assert {row["cause"] for row in diffs} == {"harness:not_replayed"}
    assert summary["not_replayed"] == [
        {"session": SESSIONS[0].isoformat(), "stage": "analyst"},
        {"session": SESSIONS[0].isoformat(), "stage": "pm"},
    ]


def test_every_float_is_compared_within_the_one_tolerance() -> None:
    """ANLZ-IDM-01 / Trap 7: 1e-9 absolute, stated once, used for every float."""
    assert matches(0.7, 0.7 + TOLERANCE / 2)
    assert not matches(0.7, 0.7 + TOLERANCE * 2)
    assert matches(1, 1.0 + TOLERANCE / 2)
    assert matches(1.0, 1)
    assert not matches(0.5, None)
    assert matches("buy", "buy")


def test_a_scan_without_a_stored_filter_trace_compares_membership_only() -> None:
    """SCAN-OBS-01: the filter trace is compared only where live stored one."""
    live = {"candidate_set": {"candidates": [{"ticker": "T01", "rank": 1}]}}

    rows = scanner_rows("2026-09-28", live, None)

    assert [(row["ticker"], row["field"], row["replay"]) for row in rows] == [
        ("T01", "rank", None)
    ]


def test_each_broker_outcome_is_one_bucket_and_resting_stops_are_not_orders() -> None:
    """EXEC-OUT-07 / EXEC-STA-05: filled, partial, rejected, dropped, pending."""
    fills = [
        {"ticker": "A", "broker_status": "filled"},
        {"ticker": "B", "broker_status": "partial"},
        {"ticker": "C", "broker_status": "rejected"},
        {"ticker": "D", "drop_reason": "unfilled at session end"},
        {"ticker": "E", "broker_status": "expired"},
        {"ticker": "F"},
        {"ticker": "G", "stop_order_key": "stop:ref:G", "broker_status": "filled"},
    ]

    row = layer3_row({"session": "2026-09-28", "fills": fills})

    assert {name: row[name] for name in row if name != "session"} == {
        "approved_buy": 0,
        "approved_sell": 0,
        "vetoed": 0,
        "submitted": 0,
        "execution_rejected": 0,
        "execution_skipped": 0,
        "filled": 1,
        "partial": 1,
        "broker_rejected": 1,
        "dropped": 2,
        "pending": 1,
    }
