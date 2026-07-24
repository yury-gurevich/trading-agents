"""ADR-0015 monitor close-lifecycle tests.

Agent: monitor
Role: prove close intent is lineage and repeated decisions are idempotent.
External I/O: none.
"""

from __future__ import annotations

from agents.monitor.position_book import active_positions
from agents.monitor.reconcile import reconcile_positions_from_latest_snapshot
from agents.monitor.settings import MonitorSettings
from agents.monitor.store import write_close_decision
from contracts.common import Explanation
from kernel import InMemoryGraphStore, Node


def test_close_decision_stays_open_without_fresh_broker_snapshot() -> None:
    """ADR-0015 section 1: without fresh broker evidence, close intent stays open."""
    graph = InMemoryGraphStore()
    position = _position(graph, "pm-run:AMD", "AMD", 19, 15924)
    close = graph.merge_node("CloseDecision", "close:AMD", {"decision": "close"})
    graph.add_edge(close, position, "CLOSES")
    _snapshot(graph, "stale", status="stale")

    reconcile_positions_from_latest_snapshot(graph, MonitorSettings())

    assert active_positions(graph) == (position,)


def test_redeciding_one_position_appends_a_fact_per_run() -> None:
    """ADR-0015 section 1: under evidence-based closure the same exit is
    re-decided every run. The graph is append-only (graph_support.py refuses
    to overwrite a property), so each decision is its own immutable fact keyed
    by its deciding run; one node with a changing run_id is not representable."""
    graph = InMemoryGraphStore()
    position = _position(graph, "pm-run:AMD", "AMD", 19, 15924)
    rationale = Explanation(summary="stop breached", evidence_refs=("monitor.stop",))

    write_close_decision(
        graph,
        monitor_run_id="monitor-run-old",
        position=position,
        decision="close",
        trigger="stop",
        rationale=rationale,
    )
    write_close_decision(
        graph,
        monitor_run_id="monitor-run-latest",
        position=position,
        decision="close",
        trigger="stop",
        rationale=rationale,
    )

    close_nodes = graph.list_nodes("CloseDecision")
    assert len(close_nodes) == 2
    assert {node.key for node in close_nodes} == {
        "monitor-run-old:pm-run:AMD:close",
        "monitor-run-latest:pm-run:AMD:close",
    }
    assert all("pnl_cents" not in node.props for node in close_nodes)


def _snapshot(graph: InMemoryGraphStore, suffix: str, *, status: str = "fresh") -> Node:
    return graph.merge_node(
        "BrokerPositionSnapshot",
        f"snapshot:{suffix}",
        {
            "run_id": "pm-run",
            "status": status,
            "created_at": f"2026-07-08T00:00:0{len(suffix)}+00:00",
            "holding_count": 0,
            "holdings": [],
        },
    )


def _position(
    graph: InMemoryGraphStore,
    key: str,
    ticker: str,
    quantity: int,
    opened_price_cents: int,
) -> Node:
    return graph.merge_node(
        "Position",
        key,
        {
            "run_id": "pm-run",
            "ticker": ticker,
            "opened_price_cents": opened_price_cents,
            "quantity": quantity,
            "stop_pct": 0.05,
            "target_pct": 0.10,
            "horizon_days": 14,
            "opened_at": "2026-07-08T00:00:00+00:00",
            "status": "open",
            "degraded": False,
        },
    )
