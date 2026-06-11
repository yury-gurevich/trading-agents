"""Supervisor agent tests.

Agent: supervisor
Role: verify message lineage, fault graph writes, and unimplemented P5 behavior.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.supervisor import SupervisorAgent
from agents.supervisor.settings import SupervisorSettings
from contracts.supervisor import CONTRACT, DispatchResult, DispatchRunRecord
from kernel import AgentFault, AgentMessage, InMemoryGraphStore, InProcessBus

if TYPE_CHECKING:
    from collections.abc import Iterator

    from kernel import Node
    from kernel.graph_support import Props


def test_record_dispatch_run_writes_one_message_per_step() -> None:
    graph = InMemoryGraphStore()
    bus = _bound_bus(graph)
    response = bus.request(
        _message(
            "record_dispatch_run",
            DispatchRunRecord(
                run_id="dispatch-1",
                steps_attempted=("scan", "analyze", "evaluate"),
                completed=True,
            ),
        )
    )
    result = DispatchResult.model_validate(response.payload)
    assert result.accepted is True
    assert _node_count(graph, "Message") == 3
    assert graph.get_node("Message", "dispatch-1:scan") is not None


def test_record_dispatch_run_is_idempotent_for_same_run_record() -> None:
    graph = InMemoryGraphStore()
    bus = _bound_bus(graph)
    record = DispatchRunRecord(
        run_id="dispatch-2",
        steps_attempted=("scan", "analyze"),
        completed=False,
        reason="analysis produced no recommendations",
    )
    bus.request(_message("record_dispatch_run", record))
    bus.request(_message("record_dispatch_run", record))
    assert _node_count(graph, "Message") == 2


def test_record_dispatch_run_writes_fault_nodes() -> None:
    graph = InMemoryGraphStore()
    bus = _bound_bus(graph, settings=SupervisorSettings(max_fault_message_chars=80))
    bus.request(
        _message(
            "record_dispatch_run",
            DispatchRunRecord(
                run_id="dispatch-with-fault",
                steps_attempted=("scan",),
                completed=False,
                faults=(_fault("x" * 120),),
            ),
        )
    )
    fault = graph.list_nodes("Fault")[0]
    assert _node_count(graph, "Fault") == 1
    assert len(str(fault.props["message"])) == 80


def test_report_fault_writes_one_fault_node() -> None:
    graph = InMemoryGraphStore()
    bus = _bound_bus(graph)
    response = bus.request(_message("report_fault", _fault("provider exploded")))
    result = DispatchResult.model_validate(response.payload)
    assert result.accepted is True
    assert _node_count(graph, "Fault") == 1


def test_report_fault_is_idempotent_for_same_fault() -> None:
    graph = InMemoryGraphStore()
    bus = _bound_bus(graph)
    fault = _fault("same failure")
    bus.request(_message("report_fault", fault))
    bus.request(_message("report_fault", fault))
    assert _node_count(graph, "Fault") == 1


def test_unknown_capability_returns_error_response() -> None:
    graph = InMemoryGraphStore()
    bus = _bound_bus(graph)
    response = bus.request(
        AgentMessage(
            sender="operator",
            recipient="supervisor",
            message_type="request",
            capability="not_real",
            payload={},
        )
    )
    assert response.message_type == "error"
    assert response.payload["error_type"] == "UnknownCapability"


def test_supervisor_contract_claims_message_and_fault_once() -> None:
    labels = tuple(
        label for label in CONTRACT.owns_graph if label in {"Message", "Fault"}
    )
    assert labels == ("Message", "Fault")


def test_record_dispatch_run_returns_rejection_when_graph_write_fails() -> None:
    agent = SupervisorAgent(InProcessBus(), graph=_BrokenGraph())
    result = agent._record_dispatch_run(
        DispatchRunRecord(
            run_id="broken-run",
            steps_attempted=("scan",),
            completed=False,
        )
    )
    assert result.accepted is False


def test_report_fault_returns_rejection_when_graph_write_fails() -> None:
    agent = SupervisorAgent(InProcessBus(), graph=_BrokenGraph())
    result = agent._report_fault(_fault("broken graph"))
    assert result.accepted is False


def _bound_bus(
    graph: InMemoryGraphStore,
    *,
    settings: SupervisorSettings | None = None,
) -> InProcessBus:
    bus = InProcessBus()
    SupervisorAgent(bus, graph=graph, settings=settings).bind()
    return bus


def _message(capability: str, payload: DispatchRunRecord | AgentFault) -> AgentMessage:
    return AgentMessage(
        sender="dispatcher",
        recipient="supervisor",
        message_type="request",
        capability=capability,
        payload=payload.model_dump(mode="json"),
    )


def _fault(message: str) -> AgentFault:
    return AgentFault(
        source_agent="provider",
        source_module="agents.provider.agent",
        capability="daily_bars",
        error_type="RuntimeError",
        message=message,
    )


def _node_count(graph: InMemoryGraphStore, label: str) -> int:
    return len(graph.list_nodes(label))


class _BrokenGraph:
    def merge_node(
        self, label: str, key: str, props: Props, *, schema_version: int = 1
    ) -> Node:
        raise RuntimeError("graph write failed")

    def add_edge(
        self, parent: Node, child: Node, edge_type: str, props: Props | None = None
    ) -> None:
        raise RuntimeError("graph write failed")

    def get_node(self, label: str, key: str) -> Node | None:
        return None

    def list_nodes(self, label: str) -> tuple[Node, ...]:
        return ()

    def ancestors(
        self, node: Node, *, max_depth: int, edge_types: set[str] | None = None
    ) -> Iterator[Node]:
        return iter(())

    def descendants(
        self, node: Node, *, max_depth: int, edge_types: set[str] | None = None
    ) -> Iterator[Node]:
        return iter(())
