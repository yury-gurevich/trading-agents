"""The 2026-09-25 live shape for the decided-stop tests (S230, DL-222/DL-223).

Agent: execution
Role: seed an adopted USB Position, its PM lineage and a 5 % resting stop.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.execution.broker_stop_actions import place_stop
from agents.execution.broker_stop_types import StopProvenance
from agents.execution.broker_stops import place_broker_stops
from agents.execution.paper_broker import PaperBroker
from agents.execution.tests.broker_stop_helpers import order_set
from contracts.positions import PositionStopThreshold, open_positions
from kernel import CollectingFaultSink

if TYPE_CHECKING:
    from agents.execution.broker import BrokerFill
    from kernel import GraphStore, Node

ADOPTED_KEY = "broker:USB:16:6050"
LINEAGE_RUN = "pm-run-3b9e7c41d2"
DECIDED_STOP_PCT = 0.0402588750356905
FALLBACK_STOP_PCT = 0.05
OPENED_CENTS = 6050
QUANTITY = 16
DECIDED_STOP_CENTS = 5806
FALLBACK_STOP_CENTS = 5747


def seed_adopted_usb(graph: GraphStore, *, quantity: int = QUANTITY) -> Node:
    """Write the broker-adopted Position exactly as monitor adoption writes it."""
    return graph.merge_node(
        "Position",
        f"broker:USB:{quantity}:{OPENED_CENTS}",
        {
            "run_id": "sched-2026-09-24",
            "ticker": "USB",
            "opened_price_cents": OPENED_CENTS,
            "quantity": quantity,
            "stop_pct": FALLBACK_STOP_PCT,
            "target_pct": 0.10,
            "horizon_days": 14,
            "opened_at": "2026-09-24T22:31:00+00:00",
            "status": "open",
            "degraded": True,
            "provenance": "reconciled-from-broker",
        },
    )


def seed_buy(
    graph: GraphStore,
    run_id: str,
    *,
    quantity: int = QUANTITY,
    stop_pct: float | None = DECIDED_STOP_PCT,
    submitted_at: str = "2026-09-18T22:40:11+00:00",
) -> Node:
    """Write one filled production buy Fill and the OrderIntent it EXECUTES."""
    fill = graph.merge_node(
        "Fill",
        f"{run_id}:USB:buy",
        {
            "ticker": "USB",
            "side": "buy",
            "status": "pending",
            "broker_status": "filled",
            "quantity": quantity,
            "price_cents": 6048,
            "broker_price_cents": OPENED_CENTS,
            "source_run_id": run_id,
            "submitted_at": submitted_at,
        },
    )
    order = graph.merge_node(
        "OrderIntent", f"{run_id}:USB", {"ticker": "USB", "stop_pct": stop_pct}
    )
    graph.add_edge(fill, order, "EXECUTES")
    return fill


def seed_usb(graph: GraphStore) -> Node:
    """Write the adopted Position plus its one exact lineage buy."""
    seed_buy(graph, LINEAGE_RUN)
    return seed_adopted_usb(graph)


def seed_usb_stop(
    graph: GraphStore, broker: PaperBroker, *, stop_pct: float = FALLBACK_STOP_PCT
) -> str:
    """Rest a stop for the adopted Position the way pre-S230 execution did."""
    ref = open_positions(graph)[0].position_ref
    threshold = PositionStopThreshold("USB", QUANTITY, ref, OPENED_CENTS, stop_pct)
    key = f"stop:{ref}:USB"
    provenance = StopProvenance("position", "active_position")
    place_stop(
        graph, broker, CollectingFaultSink(), threshold, key, provenance=provenance
    )
    return key


def usb_snapshot(graph: GraphStore, *, price_cents: int = 5840) -> Node:
    """Write the run's fresh broker snapshot carrying USB's market value."""
    holding = {
        "ticker": "USB",
        "quantity": QUANTITY,
        "avg_entry_cents": OPENED_CENTS,
        "market_value_cents": price_cents * QUANTITY,
    }
    return graph.merge_node(
        "BrokerPositionSnapshot",
        f"snapshot:{price_cents}",
        {"status": "fresh", "holdings": [holding]},
    )


def run_placement(
    graph: GraphStore, broker: PaperBroker, *, price_cents: int = 5840
) -> CollectingFaultSink:
    """Run one placement pass, as a hold run does, and return its faults."""
    sink = CollectingFaultSink()
    place_broker_stops(
        graph,
        broker,
        sink,
        order_set("pm-run-today"),
        usb_snapshot(graph, price_cents=price_cents),
        fallback_stop_pct=FALLBACK_STOP_PCT,
    )
    return sink


def live_stop_count(broker: PaperBroker) -> int:
    """Count the stops the paper broker still holds open for USB."""
    return sum(
        1
        for fill in PaperBroker.fills(broker)
        if fill.ticker == "USB"
        and fill.order_type == "stop"
        and fill.status == "pending"
    )


class RecordingPaperBroker(PaperBroker):
    """Paper broker that records every replace and the live stops at that moment."""

    def __init__(
        self, *, fail_replace: bool = False, stop_order_status: str = "new"
    ) -> None:
        """Create a paper broker; `fail_replace` makes every replace raise."""
        super().__init__(stop_order_status=stop_order_status)
        self.fail_replace = fail_replace
        self.replace_calls: list[tuple[str, int]] = []
        self.live_at_replace: list[int] = []
        self.fills_reads = 0

    def fills(self) -> tuple[BrokerFill, ...]:
        """Count every read of the broker's orders."""
        self.fills_reads += 1
        return super().fills()

    def replace_stop(
        self, broker_order_id: str, stop_price_cents: int, *, idempotency_key: str
    ) -> BrokerFill:
        """Record the call, then replace through the paper broker."""
        self.replace_calls.append((broker_order_id, stop_price_cents))
        self.live_at_replace.append(live_stop_count(self))
        if self.fail_replace:
            raise RuntimeError("paper replace failed")
        return super().replace_stop(
            broker_order_id, stop_price_cents, idempotency_key=idempotency_key
        )
