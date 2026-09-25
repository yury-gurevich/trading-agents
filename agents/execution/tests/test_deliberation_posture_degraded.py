"""Execution degraded-posture tests for S227.

Agent: execution
Role: prove degraded RunRequests hold buys without delaying exits or stops.
External I/O: none.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from agents.execution import poll as execution_poll
from agents.execution.paper_broker import PaperBroker
from agents.execution.poll import execute_pm_node
from agents.execution.settings import ExecutionSettings
from agents.execution.tests.broker_stop_helpers import (
    position as broker_position,
)
from agents.execution.tests.helpers import order, order_set
from agents.execution.tests.test_deliberation_posture import (
    _fault_props,
    _seed_pm_run,
    _sell,
)
from contracts.broker_stops import active_broker_stop_refs
from contracts.common import Money
from kernel import InMemoryGraphStore

# `find_pending` reads the wall clock, so the grace window is measured from real now.
# A pinned date expired 900 s after it was written: from 2026-09-24 22:45 UTC the
# normal-run test failed and the degraded-run test passed without exercising the
# bypass it exists to prove.
_NOW = datetime.now(tz=UTC)


def test_degraded_run_drops_buys_without_waiting_and_submits_sell() -> None:
    """EXEC-OUT-09 / EXEC-NEV-07 / EXEC-OBS-04.

    Degraded runs hold buys while exits do not wait.
    """
    payload = order_set(order("AAPL"), _sell("MSFT"))
    graph = InMemoryGraphStore()
    graph.merge_node(
        "RunRequest",
        f"run-request:{payload.run_id}",
        {
            "run_id": payload.run_id,
            "run_posture": "degraded",
            "degraded_by": [
                "unrecoverable:deliberator-manager:anthropic:unrecoverable:http_400"
            ],
        },
    )
    node = _seed_pm_run(graph, payload)
    graph.merge_node("PMRun", node.key, {"created_at": _NOW.isoformat()})
    settings = ExecutionSettings(
        deliberation_posture="binding", deliberation_grace_seconds=900
    )

    pending = execution_poll.find_pending(graph, settings=settings)

    assert [item.key for item in pending] == [node.key]
    execute_pm_node(node, graph=graph, broker=PaperBroker(), settings=settings)
    (execution,) = graph.list_nodes("ExecutionRun")
    fills = graph.list_nodes("Fill")
    fault = _fault_props(graph)

    assert [fill.props["ticker"] for fill in fills] == ["MSFT"]
    assert execution.props["submitted"] == 1
    assert execution.props["skipped"] == 1
    assert execution.props["deliberation_status"] == "held_degraded"
    assert execution.props["deliberation_posture"] == "binding"
    assert execution.props["deliberation_blocked_count"] == 1
    assert fault["severity"] == "warning"
    assert fault["error_type"] == "DeliberationHeldDegraded"
    assert "posture=degraded" in str(fault["message"])


def test_normal_run_still_waits_then_blocks_buy_after_grace() -> None:
    """EXEC-NEV-06 / EXEC-OBS-04: normal binding grace behavior is unchanged."""
    payload = order_set(order("AAPL"))
    graph = InMemoryGraphStore()
    node = _seed_pm_run(graph, payload)
    graph.merge_node("PMRun", node.key, {"created_at": _NOW.isoformat()})
    settings = ExecutionSettings(
        deliberation_posture="binding", deliberation_grace_seconds=900
    )

    assert execution_poll.find_pending(graph, settings=settings) == []
    expired = InMemoryGraphStore()
    expired_payload = payload.model_copy(update={"run_id": "pm-run-expired"})
    expired_node = _seed_pm_run(expired, expired_payload)
    expired.merge_node(
        "PMRun",
        expired_node.key,
        {"created_at": (_NOW - timedelta(seconds=901)).isoformat()},
    )
    execute_pm_node(
        expired_node, graph=expired, broker=PaperBroker(), settings=settings
    )
    (execution,) = expired.list_nodes("ExecutionRun")
    fault = _fault_props(expired)

    assert expired.list_nodes("Fill") == ()
    assert execution.props["submitted"] == 0
    assert execution.props["skipped"] == 1
    assert execution.props["deliberation_status"] == "proceeded_unvetoed"
    assert fault["severity"] == "error"
    assert fault["error_type"] == "DeliberationGraceExpired"


def test_degraded_run_still_places_protective_stops() -> None:
    """EXEC-NEV-07 / EXEC-OBS-03: degraded posture does not skip broker stops."""
    payload = order_set(order("AAPL"))
    graph = InMemoryGraphStore()
    graph.merge_node(
        "RunRequest",
        f"run-request:{payload.run_id}",
        {"run_id": payload.run_id, "run_posture": "degraded", "degraded_by": ["x"]},
    )
    node = _seed_pm_run(graph, payload)
    broker_position(graph, "held:AAPL", "AAPL", 4, opened_price_cents=10000)
    broker = PaperBroker()
    broker.submit("seed:AAPL", "AAPL", "buy", 4, Money(amount=Decimal("100.00")))

    execute_pm_node(
        node,
        graph=graph,
        broker=broker,
        settings=ExecutionSettings(deliberation_posture="binding"),
    )

    (execution,) = graph.list_nodes("ExecutionRun")
    assert execution.props["deliberation_status"] == "held_degraded"
    assert graph.list_nodes("BrokerStopOrder")
    assert active_broker_stop_refs(graph)
    assert graph.list_nodes("Fill")
    assert all(fill.props["side"] == "sell" for fill in graph.list_nodes("Fill"))
