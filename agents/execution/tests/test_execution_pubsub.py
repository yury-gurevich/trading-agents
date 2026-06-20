"""Execution pub/sub dual-mode tests — P14.5.

Agent: execution
Role: verify the execution agent subscribes to portfolio.orders.ready, submits orders,
      and publishes execution.fills.ready via claim-check; existing RPC path unaffected.
External I/O: none.
"""

from __future__ import annotations

from agents.execution.tests.helpers import order, order_set, wire
from contracts.execution import ExecutionResult
from kernel import InMemoryGraphStore, InProcessBus, ReadyEvent, claim_check_read


def _seed_order_intent_result(
    graph: InMemoryGraphStore,
    *,
    run_id: str = "run-ex-1",
) -> dict[str, object]:
    """Write an OrderIntentResult node directly (no publish) and return event dict."""
    os_ = order_set(order("AAPL"))
    graph.merge_node(
        "OrderIntentResult",
        f"orders:{run_id}",
        {"orders": os_.model_dump(mode="json")},
    )
    return ReadyEvent(
        topic="portfolio.orders.ready",
        label="OrderIntentResult",
        ref=f"orders:{run_id}",
        run_id=run_id,
    ).model_dump(mode="json")


def _wire_with_orders(
    *, run_id: str = "run-ex-1"
) -> tuple[InProcessBus, InMemoryGraphStore, dict[str, object]]:
    bus, graph, _, _ = wire()
    event = _seed_order_intent_result(graph, run_id=run_id)
    return bus, graph, event


def test_orders_ready_triggers_fills_ready() -> None:
    """EXEC-IN-03 / EXEC-TRG-02 / EXEC-OUT-06: portfolio.orders.ready → claim-check
    resolved → submit → execution.fills.ready emitted with ref."""
    bus, _, event = _wire_with_orders()
    received: list[dict[str, object]] = []
    bus.subscribe("execution.fills.ready", received.append)

    bus.publish("portfolio.orders.ready", event)

    assert len(received) == 1
    assert received[0]["topic"] == "execution.fills.ready"
    assert str(received[0]["ref"]).startswith("execution:")


def test_execution_result_node_in_graph() -> None:
    """EXEC-STA-03 / EXEC-OBS-01: ExecutionResultEvent node written to graph."""
    bus, graph, event = _wire_with_orders(run_id="run-ex-2")
    received: list[dict[str, object]] = []
    bus.subscribe("execution.fills.ready", received.append)

    bus.publish("portfolio.orders.ready", event)

    node = claim_check_read(graph, received[0])
    assert node.label == "ExecutionResultEvent"
    assert "result" in node.props


def test_execution_result_is_deserializable() -> None:
    """EXEC-TYP-03: graph node deserialises to ExecutionResult per contract."""
    bus, graph, event = _wire_with_orders(run_id="run-ex-3")
    received: list[dict[str, object]] = []
    bus.subscribe("execution.fills.ready", received.append)

    bus.publish("portfolio.orders.ready", event)

    node = claim_check_read(graph, received[0])
    result = ExecutionResult.model_validate(node.props["result"])
    assert isinstance(result, ExecutionResult)


def test_run_id_propagated_in_fills_ready_event() -> None:
    """EXEC-IDM-02 / EXEC-OUT-06: run_id threaded into fills.ready event envelope."""
    bus, _, event = _wire_with_orders(run_id="ex-run-99")
    received: list[dict[str, object]] = []
    bus.subscribe("execution.fills.ready", received.append)

    bus.publish("portfolio.orders.ready", event)

    assert received[0]["run_id"] == "ex-run-99"


def test_existing_rpc_submit_still_works() -> None:
    from agents.execution.tests.helpers import order_set as make_order_set
    from kernel import AgentMessage

    bus, _, _, _ = wire()
    os_ = make_order_set(order("AAPL"))
    msg = AgentMessage(
        sender="tester",
        recipient="execution",
        message_type="request",
        capability="submit",
        payload=os_.model_dump(mode="json"),
    )

    response = bus.request(msg)

    assert response.message_type == "response"
