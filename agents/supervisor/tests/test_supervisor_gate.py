"""Supervisor P5 gate tests.

Agent: supervisor
Role: verify hard-NO, confirmation, matrix routing, health, and flags.
External I/O: none.
"""

from __future__ import annotations

from agents.supervisor import SupervisorAgent
from agents.supervisor.domain.matrix import CAPABILITY_MATRIX
from contracts.common import Provenance
from contracts.operator import TypedIntent
from contracts.supervisor import DispatchResult
from kernel import AgentMessage, InMemoryGraphStore, InProcessBus


def test_hard_no_blocks_before_confirmation_or_matrix() -> None:
    graph = InMemoryGraphStore()
    bus = _bound_bus(graph)
    live = _dispatch(
        bus,
        _intent("run", {"stage": "live", "confirmed": "true"}),
    )
    bypass = _dispatch(bus, _intent("status", {"bypass_gate": "true"}))
    disable = _dispatch(bus, _intent("status", {"disable_supervisor": "true"}))
    assert live.accepted is False
    assert "live-stage" in str(live.rejection)
    assert "bypassing the capability gate" in str(bypass.rejection)
    assert "disabling the supervisor" in str(disable.rejection)
    assert _node_count(graph, "Message") == 0


def test_capability_matrix_routes_available_and_refuses_unavailable() -> None:
    bus = _bound_bus(InMemoryGraphStore())
    assert _dispatch(bus, _intent("status")).routed_to == "reporter.report"
    assert _dispatch(bus, _intent("explain")).routed_to == "reporter.narrative"
    run = _dispatch(bus, _intent("run", {"confirmed": "true"}))
    assert run.accepted is True
    assert run.routed_to == "orchestration.execute_run"
    approve = _dispatch(bus, _intent("approve", {"confirmed": "true"}))
    stage = _dispatch(bus, _intent("stage", {"confirmed": "true"}))
    assert approve.accepted is False
    assert "P7" in str(approve.rejection)
    assert "P8" in str(stage.rejection)
    assert CAPABILITY_MATRIX["approve"].routed_to is None


def test_confirmation_gate_writes_and_resolves_flag() -> None:
    graph = InMemoryGraphStore()
    bus = _bound_bus(graph)
    first = _dispatch(bus, _intent("run"))
    flag = graph.get_node("Flag", "flag:intent-run:warn")
    assert first.accepted is False
    assert "confirmation required" in str(first.rejection)
    assert flag is not None
    assert flag.props["status"] == "pending"
    confirmed = _dispatch(bus, _intent("run", {"confirmed": "true"}))
    resolved = graph.get_node("FlagResolution", "resolution:flag:intent-run:warn")
    assert confirmed.accepted is True
    assert resolved is not None
    assert _node_count(graph, "FlagResolution") == 1


def test_read_only_status_does_not_write_confirmation_flag() -> None:
    graph = InMemoryGraphStore()
    result = _dispatch(_bound_bus(graph), _intent("status"))
    assert result.accepted is True
    assert _node_count(graph, "Flag") == 0


def _bound_bus(graph: InMemoryGraphStore) -> InProcessBus:
    bus = InProcessBus()
    SupervisorAgent(bus, graph=graph).bind()
    return bus


def _dispatch(bus: InProcessBus, intent: TypedIntent) -> DispatchResult:
    response = bus.request(
        AgentMessage(
            sender="operator",
            recipient="supervisor",
            message_type="request",
            capability="dispatch_intent",
            payload=intent.model_dump(mode="json"),
        )
    )
    return DispatchResult.model_validate(response.payload)


def _intent(family: str, params: dict[str, str] | None = None) -> TypedIntent:
    return TypedIntent(
        family=family,  # type: ignore[arg-type]
        parameters=params or {},
        requires_confirmation=family
        in {"run", "approve", "reject", "modify", "mode", "stage"},
        provenance=Provenance(run_id=f"intent-{family}", source_agent="operator"),
    )


def _node_count(graph: InMemoryGraphStore, label: str) -> int:
    return len(graph.list_nodes(label))
