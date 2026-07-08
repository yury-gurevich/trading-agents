"""Monitor broker-reconciliation edge coverage.

Agent: monitor
Role: cover broker snapshot matching when same-quantity positions differ by basis.
External I/O: none.
"""

from __future__ import annotations

from agents.monitor.position_book import active_positions
from agents.monitor.reconcile import reconcile_positions_from_latest_snapshot
from agents.monitor.settings import MonitorSettings
from kernel import InMemoryGraphStore, Node


def test_reconcile_supersedes_same_quantity_with_wrong_entry_basis() -> None:
    graph = InMemoryGraphStore()
    stale = _position(graph, "pm-run:AMD-old", "AMD", 19, 15000)
    current = _position(graph, "pm-run:AMD", "AMD", 19, 15924)
    graph.merge_node(
        "BrokerPositionSnapshot",
        "snapshot:newer",
        {
            "run_id": "pm-run",
            "status": "fresh",
            "created_at": "2026-07-08T00:00:02+00:00",
            "holding_count": 1,
            "holdings": [
                {
                    "ticker": "AMD",
                    "quantity": 19,
                    "avg_entry_cents": 15924,
                    "market_value_cents": 304550,
                }
            ],
        },
    )

    reconcile_positions_from_latest_snapshot(graph, MonitorSettings())

    stale_node = graph.get_node("Position", stale.key)
    assert stale_node is not None
    assert stale_node.props["broker_superseded_by"] == current.key
    assert active_positions(graph) == (current,)


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
