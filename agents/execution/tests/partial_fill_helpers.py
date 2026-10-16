"""UNH's ended partial order and its graph lineage.

Agent: execution
Role: supply synthetic broker and graph facts for Sprint 280 proofs.
External I/O: none.
"""

from decimal import Decimal

from agents.execution.alpaca_orders import fill_from_order
from agents.execution.broker import BrokerFill
from contracts.common import Money
from kernel import CollectingFaultSink, InMemoryGraphStore, Node

PM_RUN = "pm-run-s280"
FILL_KEY = f"{PM_RUN}:UNH:buy"
DECIDED_STOP = 0.05650079080214057


def unh_order(**changes: object) -> dict[str, object]:
    """Return the measured order shape, with explicit per-test overrides."""
    order: dict[str, object] = {
        "id": "broker-unh",
        "client_order_id": FILL_KEY,
        "symbol": "UNH",
        "side": "buy",
        "qty": "2",
        "filled_qty": "1",
        "filled_avg_price": "401.11",
        "limit_price": "401.2",
        "status": "expired",
        "type": "limit",
        "time_in_force": "day",
        "submitted_at": "2026-10-14T22:32:00+00:00",
    }
    order.update(changes)
    return order


def mapped_unh(**changes: object) -> BrokerFill:
    """Map the synthetic broker response through the real adapter."""
    return fill_from_order(
        unh_order(**changes), FILL_KEY, Money(amount=Decimal("401.20"))
    )


def seed_unh(graph: InMemoryGraphStore) -> Node:
    """Seed the pending two-share decision and execution ancestry."""
    pm = graph.merge_node("PMRun", PM_RUN, {"approved_count": 1})
    order = graph.merge_node(
        "OrderIntent",
        f"{PM_RUN}:UNH",
        {"ticker": "UNH", "quantity": 2, "stop_pct": DECIDED_STOP},
    )
    fill = graph.merge_node(
        "Fill",
        FILL_KEY,
        {
            "ticker": "UNH",
            "side": "buy",
            "quantity": 2,
            "price_cents": 40120,
            "price_currency": "USD",
            "status": "pending",
            "source_run_id": PM_RUN,
            "broker_idempotency_key": FILL_KEY,
            "broker_order_id": "broker-unh",
            "attempt_ordinal": 0,
        },
    )
    execution = graph.merge_node("ExecutionRun", "execution-s280", {})
    graph.add_edge(fill, order, "EXECUTES")
    graph.add_edge(order, pm, "EMITTED_BY")
    graph.add_edge(pm, execution, "EXECUTED_BY")
    return fill


def adopt_unh(graph: InMemoryGraphStore) -> Node:
    """Seed the broker-adopted share carrying the fallback stop."""
    return graph.merge_node(
        "Position",
        "broker:UNH:1:40111",
        {
            "ticker": "UNH",
            "quantity": 1,
            "opened_price_cents": 40111,
            "stop_pct": 0.05,
            "provenance": "reconciled-from-broker",
            "status": "open",
        },
    )


def new_book() -> tuple[InMemoryGraphStore, CollectingFaultSink]:
    """Return a fresh pending decision and a collecting fault sink."""
    graph = InMemoryGraphStore()
    seed_unh(graph)
    return graph, CollectingFaultSink()


def stored_fill(graph: InMemoryGraphStore) -> Node:
    """Read the refreshed node instead of retaining its pre-refresh snapshot."""
    fill = graph.get_node("Fill", FILL_KEY)
    assert fill is not None
    return fill
