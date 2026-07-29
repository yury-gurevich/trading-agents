"""Monitor head-of-run position-sync poll tests.

Agent: monitor
Role: prove broker snapshots are adopted into Position state before analyst work.
External I/O: none.
"""

from __future__ import annotations

from agents.monitor.position_sync import (
    find_pending_position_sync,
    sync_positions_snapshot,
)
from agents.monitor.tests.position_sync_helpers import (
    TrackingGraph,
    position,
    position_props,
    snapshot,
)
from contracts.position_sync import POSITION_SYNC_PHASE
from contracts.positions import open_positions
from kernel import InMemoryGraphStore

_MONITOR_LABELS = {
    "MonitorRun",
    "PositionCheck",
    "CloseDecision",
    "Position",
    "MonitorDecisionResult",
}


def test_sync_removes_sold_position_before_analyst_book_read() -> None:
    """MON-IDN-02 / MON-STA-02: sold MRVL stays append-only but not active."""
    graph = InMemoryGraphStore()
    old = position(graph, "pm-run:MRVL", "MRVL", 44, 8500)
    node = snapshot(graph, "b1", holdings=())

    sync_positions_snapshot(node, graph=graph)

    current = graph.get_node("Position", old.key)
    assert current is not None
    assert current.props["status"] == "open"
    assert current.props["broker_absent"] is True
    assert current.key == old.key
    assert all(position.ticker != "MRVL" for position in open_positions(graph))


def test_sync_supersedes_changed_quantity_cleanly() -> None:
    """MON-IDN-02 / MON-STA-02: changed quantity writes one active replacement."""
    graph = InMemoryGraphStore()
    old = position(graph, "pm-run:ABT", "ABT", 96, 5100)
    node = snapshot(
        graph,
        "b2",
        holdings=(
            {
                "ticker": "ABT",
                "quantity": 191,
                "avg_entry_cents": 5100,
                "market_value_cents": 974100,
            },
        ),
    )

    sync_positions_snapshot(node, graph=graph)

    current_old = graph.get_node("Position", old.key)
    replacement = graph.get_node("Position", "broker:ABT:191:5100")
    positions = open_positions(graph)
    assert current_old is not None
    assert replacement is not None
    assert current_old.props["broker_superseded_by"] == replacement.key
    assert [(position.ticker, position.quantity) for position in positions] == [
        ("ABT", 191)
    ]


def test_sync_stale_snapshot_never_adopts_book() -> None:
    """MON-IDN-02 / MON-STA-02: planted stale snapshot writes zero Positions."""
    graph = TrackingGraph()
    position(graph, "pm-run:MRVL", "MRVL", 44, 8500)
    node = snapshot(graph, "b3", status="stale", holdings=())
    before = position_props(graph)
    graph.reset_tracking()

    sync_positions_snapshot(node, graph=graph)

    assert graph.position_writes == 0
    assert position_props(graph) == before
    marker = graph.list_nodes("MonitorRun")[0]
    assert marker.props["position_book_status"] == "stale"


def test_sync_marker_stays_inside_monitor_owned_labels() -> None:
    """MON-IDN-02: planted sync marker writes only monitor-owned labels."""
    graph = TrackingGraph()
    node = snapshot(graph, "b4", status="stale", holdings=())
    graph.reset_tracking()

    sync_positions_snapshot(node, graph=graph)

    assert set(graph.written_labels) <= _MONITOR_LABELS
    assert graph.written_labels == ["MonitorRun"]
    marker = graph.list_nodes("MonitorRun")[0]
    assert marker.props["phase"] == POSITION_SYNC_PHASE


def test_sync_reconcile_twice_is_noop() -> None:
    """MON-IDM-02 / MON-STA-02: planted duplicate sync does not duplicate book."""
    graph = InMemoryGraphStore()
    old = position(graph, "pm-run:ABT", "ABT", 96, 5100)
    node = snapshot(
        graph,
        "b5",
        holdings=(
            {
                "ticker": "ABT",
                "quantity": 191,
                "avg_entry_cents": 5100,
                "market_value_cents": 974100,
            },
        ),
    )

    sync_positions_snapshot(node, graph=graph)
    before = position_props(graph)
    sync_positions_snapshot(node, graph=graph)

    assert position_props(graph) == before
    current_old = graph.get_node("Position", old.key)
    assert current_old is not None
    assert current_old.props["broker_superseded_by"]
    assert len(graph.list_nodes("Position")) == 2
    assert len(graph.list_nodes("MonitorRun")) == 1
    assert find_pending_position_sync(graph) == []
