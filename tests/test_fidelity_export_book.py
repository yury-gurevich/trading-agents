"""S237 export: the held book and the benchmark, as the live stages read them.

Agent: tooling
Role: prove the export carries the Position facts live read and names what it lacks.
External I/O: local tmp files only.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from scripts.fidelity_export_outcomes import benchmark_gap
from scripts.fidelity_exporter import export_sessions
from tests.fidelity_fleet import FleetDay, fleet_graph
from tests.fidelity_fleet_data import HELD_ONLY, SESSIONS

if TYPE_CHECKING:
    from pathlib import Path

    from kernel.graph_memory import InMemoryGraphStore

FIRST, SECOND = (f"sched-{day.isoformat()}" for day in SESSIONS[:2])


def _export(graph: InMemoryGraphStore, out: Path) -> dict[str, dict[str, Any]]:
    paths = export_sessions(graph, start=SESSIONS[0], end=SESSIONS[-1], out=out)
    return {path.stem: json.loads(path.read_text(encoding="utf-8")) for path in paths}


def test_the_book_is_the_position_facts_the_live_stages_read(tmp_path: Path) -> None:
    """PM-IDN-01 / PM-NEV-06: the active Position per holding, at its adoption mark."""
    added = (("T03", 2_500, 2_700), (HELD_ONLY, 1_000, 7_000))
    graph = fleet_graph(
        (FleetDay(SESSIONS[0]), FleetDay(SESSIONS[1], holdings=added)),
        git_sha="abc123",
    )

    sessions = _export(graph, tmp_path / "export")

    first = {row["props"]["ticker"]: row for row in sessions[FIRST]["positions"]}
    second = {row["props"]["ticker"]: row for row in sessions[SECOND]["positions"]}
    assert first["T03"]["key"] == "broker:T03:2000:2600"
    assert second["T03"]["key"] == "broker:T03:2500:2700"
    assert second[HELD_ONLY]["key"] == first[HELD_ONLY]["key"]
    assert (
        second[HELD_ONLY]["props"]["broker_market_value_cents"]
        == first[HELD_ONLY]["props"]["broker_market_value_cents"]
    )
    assert json.dumps(sessions[FIRST]["positions"]).count("broker_superseded") == 0
    assert sessions[SECOND]["not_persisted"] == [
        "active_broker_stop_refs",
        "held_stops",
    ]


def test_a_stale_book_names_the_held_positions(tmp_path: Path) -> None:
    """PM-OBS-01 / DRIFT-039: a book the broker did not refresh cannot be rebuilt."""
    graph = fleet_graph((FleetDay(SESSIONS[0], stale_book=True),), git_sha="abc123")

    session = _export(graph, tmp_path / "export")[FIRST]

    assert session["positions"] == []
    assert session["not_persisted"] == [
        "active_broker_stop_refs",
        "held_positions",
        "held_stops",
    ]


def test_a_benchmark_is_named_only_on_evidence_live_used_one(tmp_path: Path) -> None:
    """SCAN-OUT-06 / SCAN-OUT-07: an empty stored benchmark is not by itself a gap."""
    with_spy = fleet_graph((FleetDay(SESSIONS[0]),), git_sha="abc123")
    without = fleet_graph((FleetDay(SESSIONS[0], benchmark=False),), git_sha="abc123")
    stored = _export(with_spy, tmp_path / "with")[FIRST]
    unstored = _export(without, tmp_path / "without")[FIRST]
    snapshot = stored["market"]["snapshot"]

    assert "benchmark" not in stored["not_persisted"]
    assert "benchmark" not in unstored["not_persisted"]
    assert benchmark_gap(snapshot, stored["scanner"], stored["analyst"]) is False
    blank = {**snapshot, "benchmark": []}
    assert benchmark_gap(blank, stored["scanner"], stored["analyst"]) is True
    assert (
        benchmark_gap(
            unstored["market"]["snapshot"], unstored["scanner"], unstored["analyst"]
        )
        is False
    )
