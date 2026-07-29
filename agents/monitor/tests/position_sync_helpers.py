"""Monitor position-sync test helpers.

Agent: monitor
Role: provide compact graph fixtures for broker-snapshot sync tests.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from contracts.position_sync import RUN_REQUEST_LABEL, SNAPSHOT_LABEL, run_request_key
from kernel import InMemoryGraphStore

if TYPE_CHECKING:
    from collections.abc import Mapping

    from kernel import Node


def snapshot(
    graph: InMemoryGraphStore,
    run_id: str,
    *,
    status: str = "fresh",
    holdings: tuple[object, ...],
) -> Node:
    graph.merge_node(
        RUN_REQUEST_LABEL,
        run_request_key(run_id),
        {"run_id": run_id, "tickers": ("AAPL",)},
    )
    return graph.merge_node(
        SNAPSHOT_LABEL,
        f"snapshot:{run_id}",
        {
            "run_id": run_id,
            "status": status,
            "created_at": "2026-07-28T00:00:00+00:00",
            "holding_count": len(holdings),
            "holdings": list(holdings),
        },
    )


def position(
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
            "opened_at": "2026-07-28T00:00:00+00:00",
            "status": "open",
            "degraded": False,
        },
    )


def position_props(graph: InMemoryGraphStore) -> dict[str, dict[str, object]]:
    return {node.key: dict(node.props) for node in graph.list_nodes("Position")}


class TrackingGraph(InMemoryGraphStore):
    """In-memory graph that records writes made after fixture setup."""

    def __init__(self) -> None:
        super().__init__()
        self.position_writes = 0
        self.written_labels: list[str] = []

    def reset_tracking(self) -> None:
        self.position_writes = 0
        self.written_labels = []

    def merge_node(
        self,
        label: str,
        key: str,
        props: Mapping[str, Any],
        *,
        schema_version: int = 1,
    ) -> Node:
        self.written_labels.append(label)
        if label == "Position":
            self.position_writes += 1
        return super().merge_node(label, key, props, schema_version=schema_version)
