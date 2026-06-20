"""Monitor pub/sub dual-mode tests — P14.6.

Agent: monitor
Role: verify the monitor subscribes to execution.fills.ready, checks positions, and
      publishes monitor.decisions.ready via claim-check; existing RPC path unaffected.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.monitor.tests.helpers import bar, wire_monitor
from contracts.common import Provenance
from contracts.execution import ExecutionResult
from contracts.monitor import CloseDecisionSet
from kernel import InMemoryGraphStore, InProcessBus, ReadyEvent, claim_check_read

if TYPE_CHECKING:
    from contracts.provider import OHLCVBar


def _bars() -> tuple[OHLCVBar, ...]:
    return (bar("AAPL", 2, close=150.0), bar("AAPL", 0, close=155.0))


def _minimal_exec_result(*, run_id: str = "exec-run-1") -> ExecutionResult:
    return ExecutionResult(
        run_id=run_id,
        stage="paper",
        fills=(),
        submitted=0,
        rejected=0,
        provenance=Provenance(
            run_id=run_id,
            source_agent="execution",
            graph_node_id=f"Fill:{run_id}",
        ),
    )


def _seed_execution_result(
    graph: InMemoryGraphStore,
    *,
    run_id: str = "run-mon-1",
    exec_run_id: str = "exec-run-1",
) -> dict[str, object]:
    """Write ExecutionResultEvent node directly and return event dict."""
    result = _minimal_exec_result(run_id=exec_run_id)
    graph.merge_node(
        "ExecutionResultEvent",
        f"execution:{run_id}",
        {"result": result.model_dump(mode="json")},
    )
    return ReadyEvent(
        topic="execution.fills.ready",
        label="ExecutionResultEvent",
        ref=f"execution:{run_id}",
        run_id=run_id,
    ).model_dump(mode="json")


def _wire_with_fills(
    *, run_id: str = "run-mon-1"
) -> tuple[InProcessBus, InMemoryGraphStore, dict[str, object]]:
    bus, graph, _, _ = wire_monitor(bars=_bars())
    event = _seed_execution_result(graph, run_id=run_id)
    return bus, graph, event


def test_fills_ready_triggers_decisions_ready() -> None:
    """MON-TRG-02 / MON-IN-03 / MON-OUT-06: event path; decisions.ready published."""
    bus, _, event = _wire_with_fills()
    received: list[dict[str, object]] = []
    bus.subscribe("monitor.decisions.ready", received.append)

    bus.publish("execution.fills.ready", event)

    assert len(received) == 1
    assert received[0]["topic"] == "monitor.decisions.ready"
    assert str(received[0]["ref"]).startswith("monitor:")


def test_monitor_decision_result_node_in_graph() -> None:
    """MON-STA-02 / MON-OBS-01: MonitorDecisionResult node written to graph."""
    bus, graph, event = _wire_with_fills(run_id="run-mon-2")
    received: list[dict[str, object]] = []
    bus.subscribe("monitor.decisions.ready", received.append)

    bus.publish("execution.fills.ready", event)

    node = claim_check_read(graph, received[0])
    assert node.label == "MonitorDecisionResult"
    assert "decisions" in node.props


def test_monitor_decision_result_is_deserializable() -> None:
    """MON-TYP-02: graph node deserialises to CloseDecisionSet per contract."""
    bus, graph, event = _wire_with_fills(run_id="run-mon-3")
    received: list[dict[str, object]] = []
    bus.subscribe("monitor.decisions.ready", received.append)

    bus.publish("execution.fills.ready", event)

    node = claim_check_read(graph, received[0])
    decisions = CloseDecisionSet.model_validate(node.props["decisions"])
    assert isinstance(decisions, CloseDecisionSet)


def test_run_id_propagated_in_decisions_ready_event() -> None:
    """MON-IDM-03: run_id threaded from fills.ready into decisions.ready event."""
    bus, _, event = _wire_with_fills(run_id="mon-run-99")
    received: list[dict[str, object]] = []
    bus.subscribe("monitor.decisions.ready", received.append)

    bus.publish("execution.fills.ready", event)

    assert received[0]["run_id"] == "mon-run-99"


def test_existing_rpc_check_positions_still_works() -> None:
    from contracts.monitor import MonitorRequest
    from kernel import AgentMessage

    bus, _, _ = _wire_with_fills()
    msg = AgentMessage(
        sender="tester",
        recipient="monitor",
        message_type="request",
        capability="check_positions",
        payload=MonitorRequest(run_id="rpc-test").model_dump(mode="json"),
    )

    response = bus.request(msg)

    assert response.message_type == "response"
