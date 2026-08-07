"""Execution broker-stop replacement-chain tests.

Agent: execution
Role: prove cancelled stop facts can be replaced without weakening active-stop
      idempotency.
External I/O: none.
"""

from __future__ import annotations

from agents.execution.broker_stops import place_broker_stops
from agents.execution.tests.broker_stop_helpers import (
    PendingStopBroker,
    order_set,
    position,
)
from contracts.broker_stops import (
    BROKER_STOP_ORDER_LABEL,
    active_broker_stop_orders,
    active_broker_stop_refs,
    broker_stop_order_key,
    next_broker_stop_order_key,
)
from contracts.positions import open_positions
from kernel import CollectingFaultSink, InMemoryGraphStore, Node


def test_cancelled_stop_is_replaced_on_next_run() -> None:
    """EXEC-OBS-03 / EXEC-IDN-03 / EXEC-DEP-04: cancelled stops retry."""
    graph = InMemoryGraphStore()
    broker = PendingStopBroker()
    sink = CollectingFaultSink()
    ref = _held_position(graph)
    base_key = broker_stop_order_key(ref, "AAPL")
    _stop_fact(graph, base_key, ref, cancelled_at="2026-08-07T00:00:00+00:00")

    place_broker_stops(
        graph,
        broker,
        sink,
        order_set("pm-next"),
        _snapshot(graph, quantity=4),
        fallback_stop_pct=0.05,
    )

    replacement_key = f"{base_key}#1"
    replacement = graph.get_node(BROKER_STOP_ORDER_LABEL, replacement_key)
    assert replacement is not None
    assert "cancelled_at" not in replacement.props
    assert active_broker_stop_refs(graph) == frozenset({ref})
    assert broker.submitted == [replacement_key]
    assert _unprotected_faults(sink) == []


def test_replacement_reaches_broker_under_new_client_order_id() -> None:
    """EXEC-NEV-03 / EXEC-IDM-02: replacement uses a fresh broker key."""
    graph = InMemoryGraphStore()
    broker = PendingStopBroker()
    ref = _held_position(graph)
    base_key = broker_stop_order_key(ref, "AAPL")
    _stop_fact(graph, base_key, ref, cancelled_at="2026-08-07T00:00:00+00:00")

    place_broker_stops(
        graph,
        broker,
        CollectingFaultSink(),
        order_set("pm-next"),
        _snapshot(graph, quantity=4),
        fallback_stop_pct=0.05,
    )

    replacement_key = f"{base_key}#1"
    fill = graph.get_node("Fill", replacement_key)
    replacement = graph.get_node(BROKER_STOP_ORDER_LABEL, replacement_key)
    assert broker.submitted == [replacement_key]
    assert fill is not None
    assert fill.props["broker_idempotency_key"] == replacement_key
    assert replacement is not None
    assert replacement.props["broker_order_id"] == f"broker:{replacement_key}"


def test_active_stop_still_blocks_duplicate_submission() -> None:
    """EXEC-OBS-03 / EXEC-IDM-02: active stops are never double-placed."""
    graph = InMemoryGraphStore()
    broker = PendingStopBroker()
    sink = CollectingFaultSink()
    ref = _held_position(graph)
    base_key = broker_stop_order_key(ref, "AAPL")
    _stop_fact(graph, base_key, ref)

    place_broker_stops(
        graph,
        broker,
        sink,
        order_set("pm-next"),
        _snapshot(graph, quantity=4),
        fallback_stop_pct=0.05,
    )

    assert broker.submitted == []
    assert len(graph.list_nodes(BROKER_STOP_ORDER_LABEL)) == 1
    assert active_broker_stop_refs(graph) == frozenset({ref})
    assert sink.faults == []


def test_replacement_chain_extends_past_first_suffix() -> None:
    """EXEC-OBS-03 / EXEC-IDN-03: cancelled chains extend to the first free key."""
    graph = InMemoryGraphStore()
    broker = PendingStopBroker()
    ref = _held_position(graph)
    base_key = broker_stop_order_key(ref, "AAPL")
    _stop_fact(graph, base_key, ref, cancelled_at="2026-08-07T00:00:00+00:00")
    _stop_fact(graph, f"{base_key}#1", ref, cancelled_at="2026-08-07T01:00:00+00:00")

    place_broker_stops(
        graph,
        broker,
        CollectingFaultSink(),
        order_set("pm-next"),
        _snapshot(graph, quantity=4),
        fallback_stop_pct=0.05,
    )

    replacement_key = f"{base_key}#2"
    assert broker.submitted == [replacement_key]
    assert tuple(order.key for order in active_broker_stop_orders(graph)) == (
        replacement_key,
    )


def test_next_broker_stop_order_key_is_read_only() -> None:
    """EXEC-OBS-03 / EXEC-IDN-03: key selection reads facts without writes."""
    graph = InMemoryGraphStore()
    ref = _held_position(graph)
    base_key = broker_stop_order_key(ref, "AAPL")
    stop = _stop_fact(graph, base_key, ref, cancelled_at="2026-08-07T00:00:00+00:00")
    position_node = graph.get_node("Position", "held:AAPL")
    assert position_node is not None
    graph.add_edge(position_node, stop, "PROTECTED_BY")
    before = _graph_census(graph)

    assert next_broker_stop_order_key(graph, ref, "AAPL") == f"{base_key}#1"

    assert _graph_census(graph) == before


def _held_position(graph: InMemoryGraphStore) -> str:
    position(graph, "held:AAPL", "AAPL", 4, opened_price_cents=10000)
    return open_positions(graph)[0].position_ref


def _snapshot(graph: InMemoryGraphStore, *, quantity: int) -> Node:
    return graph.merge_node(
        "BrokerPositionSnapshot",
        "snapshot",
        {"status": "fresh", "holdings": ({"ticker": "AAPL", "quantity": quantity},)},
    )


def _stop_fact(
    graph: InMemoryGraphStore,
    key: str,
    position_ref: str,
    *,
    cancelled_at: str | None = None,
) -> Node:
    props: dict[str, object] = {
        "ticker": "AAPL",
        "position_ref": position_ref,
        "stop_price_cents": 9500,
        "stop_pct": 0.05,
        "stop_pct_source": "position",
        "broker_order_id": f"broker:{key}",
        "placed_at": "2026-08-07T00:00:00+00:00",
    }
    if cancelled_at is not None:
        props["cancelled_at"] = cancelled_at
    return graph.merge_node(BROKER_STOP_ORDER_LABEL, key, props)


def _unprotected_faults(sink: CollectingFaultSink) -> list[object]:
    return [fault for fault in sink.faults if fault.error_type == "UnprotectedPosition"]


def _graph_census(graph: InMemoryGraphStore) -> tuple[object, object]:
    nodes = tuple(
        (
            label,
            key,
            node.schema_version,
            tuple(sorted(node.props.items())),
        )
        for (label, key), node in sorted(graph._nodes.items(), key=lambda item: item[0])
    )
    return nodes, tuple(graph._edges)
