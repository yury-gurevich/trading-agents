"""S237 export: what each scheduled live run saw and decided, read and never written.

Agent: tooling
Role: prove the exporter reads live shapes, writes nothing, and names what it lacks.
External I/O: local tmp files only.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from scripts.fidelity_exporter import export_sessions, refuse_worktree_out
from tests.fidelity_fleet import (
    FleetDay,
    child,
    fleet_graph,
    pm_node,
    resume_from_analyst,
)
from tests.fidelity_fleet_data import SESSIONS
from tests.fidelity_fleet_outcomes import execute

from contracts.portfolio_manager import OrderIntentSet
from kernel.graph_memory import InMemoryGraphStore

ROOT = Path(__file__).resolve().parents[1]
FIRST, SECOND = (f"sched-{day.isoformat()}" for day in SESSIONS[:2])


class TrackingGraph(InMemoryGraphStore):
    """In-memory store that counts writes once counting is switched on."""

    def __init__(self) -> None:
        super().__init__()
        self.counting = False
        self.writes = 0

    def merge_node(self, *args: Any, **kwargs: Any) -> Any:
        self.writes += int(self.counting)
        return super().merge_node(*args, **kwargs)

    def add_edge(self, *args: Any, **kwargs: Any) -> None:
        self.writes += int(self.counting)
        super().add_edge(*args, **kwargs)


def _export(graph: InMemoryGraphStore, out: Path) -> dict[str, dict[str, Any]]:
    paths = export_sessions(graph, start=SESSIONS[0], end=SESSIONS[-1], out=out)
    return {path.stem: json.loads(path.read_text(encoding="utf-8")) for path in paths}


def test_a9_one_json_per_scheduled_run_read_and_never_written(tmp_path: Path) -> None:
    """SCAN-OBS-01 / ANLZ-OBS-01 / PM-OBS-01 / RPT-NEV-02: read-only, sched-* only."""
    graph = TrackingGraph()
    fleet_graph(
        (
            FleetDay(SESSIONS[0]),
            FleetDay(SESSIONS[1], through_pm=False),
            FleetDay(SESSIONS[1], run_id="manual-2026-09-29"),
        ),
        git_sha="abc123",
        graph=graph,
    )
    resumed_pm = resume_from_analyst(graph, SECOND)
    market = graph.get_node("MarketData", f"market-data:{SECOND}")
    assert market is not None
    original_scan = child(graph, market, "SCANNED_BY")
    graph.counting = True

    sessions = _export(graph, tmp_path / "export")

    assert graph.writes == 0
    assert sorted(sessions) == [FIRST, SECOND]
    assert sessions[FIRST]["resumed"] is False
    resumed = sessions[SECOND]
    assert resumed["resumed"] is True
    assert resumed["scanner"]["key"] == original_scan.key
    assert resumed["pm"]["key"] == resumed_pm.key
    assert resumed["analyst"]["recommendation_set"]["recommendations"]


def test_a10_the_export_refuses_the_worktree() -> None:
    """RPT-NEV-02: exported vendor bars are never written into the public repo."""
    with pytest.raises(ValueError, match="inside the worktree"):
        refuse_worktree_out(ROOT / "fidelity-export")
    with pytest.raises(ValueError, match="inside the worktree"):
        export_sessions(
            InMemoryGraphStore(),
            start=SESSIONS[0],
            end=SESSIONS[0],
            out=ROOT / "fidelity-export",
        )
    assert not (ROOT / "fidelity-export").exists()


def test_fills_are_the_pm_runs_by_source_run_id_with_broker_status(
    tmp_path: Path,
) -> None:
    """EXEC-STA-05 / EXEC-OUT-07: a fill belongs to its PMRun by source_run_id."""
    graph = fleet_graph(
        (FleetDay(SESSIONS[0]), FleetDay(SESSIONS[1])), git_sha="abc123"
    )
    first, second = pm_node(graph, FIRST), pm_node(graph, SECOND)
    ticker_a, ticker_b = _approved(first)[:2]
    execute(graph, first, {ticker_a: "filled", ticker_b: "rejected"})
    execute(graph, second, {_approved(second)[0]: "dropped"})

    sessions = _export(graph, tmp_path / "export")

    fills = sessions[FIRST]["fills"]
    assert {(fill["ticker"], fill.get("broker_status")) for fill in fills} == {
        (ticker_a, "filled"),
        (ticker_b, "rejected"),
    }
    assert {fill["source_run_id"] for fill in fills} == {first.key}
    assert all(fill["status"] == "pending" for fill in fills)
    (dropped,) = sessions[SECOND]["fills"]
    assert dropped["drop_reason"] == "unfilled at session end"


def test_held_stops_are_named_not_persisted_and_never_attached(tmp_path: Path) -> None:
    """ANLZ-IDM-01 / DRIFT-074: what the analyst read at run time is not stored."""
    graph = fleet_graph((FleetDay(SESSIONS[0]),), git_sha="abc123")
    graph.merge_node(
        "BrokerStopOrder",
        "stop:ref-t03:T03",
        {
            "ticker": "T03",
            "position_ref": "ref-t03",
            "stop_price_cents": 2_470,
            "broker_order_id": "broker-stop-t03",
            "placed_at": "2026-09-01T22:40:00+00:00",
        },
    )
    empty = fleet_graph((FleetDay(SESSIONS[0], holdings=()),), git_sha="abc123")

    held = _export(graph, tmp_path / "held")[FIRST]
    flat = _export(empty, tmp_path / "flat")[FIRST]

    assert json.dumps(held).count("broker-stop-t03") == 0  # a cheap failure message
    assert "held_stop_inputs" not in held
    assert {"held_stops", "active_broker_stop_refs"} <= set(held["not_persisted"])
    assert flat["not_persisted"] == []


def _approved(pm: Any) -> list[str]:
    order_set = OrderIntentSet.model_validate(pm.props["order_intent_set"])
    return [intent.ticker for intent in order_set.approved]
