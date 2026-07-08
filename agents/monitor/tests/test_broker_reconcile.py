"""Monitor broker-snapshot reconciliation tests.

Agent: monitor
Role: verify Position adoption from BrokerPositionSnapshot without broker access.
External I/O: none.
"""

from __future__ import annotations

from agents.monitor.position_book import active_positions
from agents.monitor.reconcile import reconcile_positions_from_latest_snapshot
from agents.monitor.settings import MonitorSettings
from agents.monitor.store import open_positions
from kernel import InMemoryGraphStore, Node


def test_reconcile_positions_from_snapshot_creates_broker_positions_once() -> None:
    graph = InMemoryGraphStore()
    _snapshot(
        graph,
        "newer",
        holdings=(
            {
                "ticker": "AMD",
                "quantity": 19,
                "avg_entry_cents": 15924,
                "market_value_cents": 304550,
            },
        ),
    )

    reconcile_positions_from_latest_snapshot(graph, MonitorSettings())
    reconcile_positions_from_latest_snapshot(graph, MonitorSettings())

    positions = graph.list_nodes("Position")
    assert len(positions) == 1
    assert positions[0].key == "broker:AMD:19:15924"
    assert positions[0].props["provenance"] == "reconciled-from-broker"
    assert positions[0].props["quantity"] == 19
    assert positions[0].props["opened_price_cents"] == 15924
    assert active_positions(graph) == positions


def test_reconcile_positions_marks_absent_and_superseded_positions() -> None:
    graph = InMemoryGraphStore()
    old = _position(graph, "pm-run:CSCO", "CSCO", 88, 6400)
    extra = _position(graph, "pm-run:HPE", "HPE", 229, 1800)
    _snapshot(graph, "stale", status="stale")
    _snapshot(
        graph,
        "newer",
        holdings=(
            "malformed",
            {"ticker": "", "quantity": 1, "avg_entry_cents": 1},
            {"ticker": "ZERO", "quantity": 0, "avg_entry_cents": 1},
            {
                "ticker": "CSCO",
                "quantity": 177,
                "avg_entry_cents": 6666,
                "market_value_cents": 1179882,
            },
        ),
    )

    reconcile_positions_from_latest_snapshot(graph, MonitorSettings())

    old_key = old.key
    extra_key = extra.key
    new = graph.get_node("Position", "broker:CSCO:177:6666")
    old_node = graph.get_node("Position", old_key)
    extra_node = graph.get_node("Position", extra_key)
    assert new is not None
    assert old_node is not None
    assert extra_node is not None
    assert old_node.props["broker_superseded_by"] == new.key
    assert extra_node.props["broker_absent"] is True
    assert [node.key for node in active_positions(graph)] == [new.key]


def test_reconcile_positions_keeps_matching_lineage_position() -> None:
    graph = InMemoryGraphStore()
    existing = _position(graph, "pm-run:AMD", "AMD", 19, 15924)
    _snapshot(
        graph,
        "newer",
        holdings=(
            {
                "ticker": "AMD",
                "quantity": 19,
                "avg_entry_cents": 15924,
                "market_value_cents": 304550,
            },
        ),
    )

    reconcile_positions_from_latest_snapshot(graph, MonitorSettings())

    assert graph.list_nodes("Position") == (existing,)
    assert active_positions(graph) == (existing,)


def test_reconcile_positions_noops_without_a_fresh_snapshot() -> None:
    graph = InMemoryGraphStore()
    _snapshot(graph, "stale", status="stale")

    reconcile_positions_from_latest_snapshot(graph, MonitorSettings())

    assert graph.list_nodes("Position") == ()


def test_active_position_helpers_filter_closed_positions() -> None:
    graph = InMemoryGraphStore()
    open_node = _position(graph, "pm-run:AMD", "AMD", 19, 15924)
    status_closed = _position(graph, "pm-run:MRVL", "MRVL", 44, 8500, status="closed")
    close_closed = _position(graph, "pm-run:HPE", "HPE", 229, 1800)
    close = graph.merge_node("CloseDecision", "close:HPE", {"decision": "close"})
    graph.add_edge(close, close_closed, "CLOSES")

    assert active_positions(graph) == (open_node,)
    assert open_positions(graph, (open_node, status_closed, close_closed)) == (
        open_node,
        status_closed,
    )


def test_reconcile_positions_returns_existing_broker_key_if_present() -> None:
    graph = InMemoryGraphStore()
    existing = _position(graph, "broker:AMD:19:15924", "AMD", 19, 15924)
    graph.merge_node("Position", existing.key, {"broker_absent": True})
    _snapshot(
        graph,
        "newer",
        holdings=(
            {
                "ticker": "AMD",
                "quantity": 19,
                "avg_entry_cents": 15924,
                "market_value_cents": 304550,
            },
        ),
    )

    reconcile_positions_from_latest_snapshot(graph, MonitorSettings())

    assert len(graph.list_nodes("Position")) == 1


def _snapshot(
    graph: InMemoryGraphStore,
    suffix: str,
    *,
    status: str = "fresh",
    holdings: tuple[object, ...] = (),
) -> Node:
    return graph.merge_node(
        "BrokerPositionSnapshot",
        f"snapshot:{suffix}",
        {
            "run_id": "pm-run",
            "status": status,
            "created_at": f"2026-07-08T00:00:0{len(suffix)}+00:00",
            "holding_count": len(holdings),
            "holdings": list(holdings),
        },
    )


def _position(
    graph: InMemoryGraphStore,
    key: str,
    ticker: str,
    quantity: int,
    opened_price_cents: int,
    **extra: object,
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
            **extra,
        },
    )
