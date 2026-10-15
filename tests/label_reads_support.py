"""S279 label-read counters and deterministic graph books.

Agent: tests
Role: count whole-label reads and seed exact lineage without external dependencies.
External I/O: none.
"""

from __future__ import annotations

from collections import Counter
from typing import TYPE_CHECKING

from agents.execution.tests.broker_stop_helpers import TrackingBroker
from agents.execution.tests.drop_sweep_helpers import (
    broker_order,
    seed_fill_lineage,
    stop_fact,
)
from kernel import InMemoryGraphStore

if TYPE_CHECKING:
    from kernel import Node

WIDTHS = {"AAA": 0.02, "BBB": 0.07, "CCC": 0.035}
PRICES = {"AAA": 9700, "BBB": 10000, "CCC": 10000}


class LabelReadCounter(InMemoryGraphStore):
    """Count each list_nodes call by label, without changing store semantics."""

    def __init__(self) -> None:
        super().__init__()
        self.listed: Counter[str] = Counter()

    def list_nodes(self, label: str) -> tuple[Node, ...]:
        self.listed[label] += 1
        return super().list_nodes(label)


def seed_sweep(graph: LabelReadCounter) -> TrackingBroker:
    """Earlier-run pending limit, filled limit and tracked broker stop, in order."""
    pending = broker_order("old-run:AAA:buy", "AAA")
    filled = broker_order("old-run:BBB:buy", "BBB", status="filled")
    stop = broker_order("stop:held:CCC", "CCC", side="sell", order_type="stop")
    for order in (pending, filled):
        seed_fill_lineage(graph, "old-run", order.idempotency_key, order.ticker)
    stop_fact(graph, stop.idempotency_key, stop.ticker, stop.broker_order_id)
    return TrackingBroker(broker_fills=(pending, filled, stop))


def seed_book(graph: LabelReadCounter, *, adopted: bool = True) -> tuple[Node, ...]:
    """Three tickers have distinct decided widths and exact filled-buy lineage."""
    positions = []
    for quantity, (ticker, width) in enumerate(WIDTHS.items(), start=2):
        position = graph.merge_node(
            "Position",
            f"held:{ticker}",
            {
                "ticker": ticker,
                "quantity": quantity,
                "opened_price_cents": 10000,
                "stop_pct": 0.05 if adopted else width,
                "provenance": "reconciled-from-broker" if adopted else "fill",
            },
        )
        order = graph.merge_node(
            "OrderIntent", f"intent:{ticker}", {"ticker": ticker, "stop_pct": width}
        )
        fill = graph.merge_node(
            "Fill",
            f"buy:{ticker}",
            {
                "ticker": ticker,
                "side": "buy",
                "quantity": quantity,
                "broker_price_cents": 10000,
                "broker_status": "filled",
                "source_run_id": f"pm-run-{ticker}",
            },
        )
        graph.add_edge(fill, order, "EXECUTES")
        positions.append(position)
    return tuple(positions)
