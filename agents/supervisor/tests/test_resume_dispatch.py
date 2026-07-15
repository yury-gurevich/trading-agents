"""Supervisor-to-orchestration resume dispatch tests.

Agent: supervisor
Role: prove confirmation wording, typed RPC routing, and validation failures.
External I/O: none; graph and bus are in-memory.
"""

from __future__ import annotations

from agents.supervisor import SupervisorAgent
from agents.supervisor.domain.gate import dispatch_intent
from contracts.common import Provenance
from contracts.operator import TypedIntent
from contracts.supervisor import DispatchResult
from kernel import AgentMessage, InMemoryGraphStore, InProcessBus
from orchestration.resume import bind_resume_run
from orchestration.start import place_run_request


def test_resume_is_double_gated_then_places_audited_child_run() -> None:
    graph = _source_graph()
    bus = _bound_bus(graph)
    params = {"run_id": "source", "from_stage": "provider"}

    gated = _dispatch(bus, _intent(params))
    confirmed = _dispatch(bus, _intent({**params, "confirmed": "true"}))

    assert gated.accepted is False
    assert (
        "re-running from portfolio manager will submit new orders at the broker"
        in str(gated.rejection)
    )
    assert confirmed.accepted is True
    assert confirmed.routed_to == "orchestration.resume_run"
    child = graph.get_node("RunRequest", "run-request:source-resume-provider")
    assert child is not None
    assert tuple(graph.descendants(child, max_depth=1, edge_types={"RESUMES"}))
    assert len(graph.list_nodes("Message")) == 1


def test_monitor_confirmation_is_safe_and_missing_upstream_is_explained() -> None:
    graph = _source_graph()
    bus = _bound_bus(graph)
    params = {"run_id": "source", "from_stage": "monitor"}
    gated = _dispatch(bus, _intent(params))
    confirmed = _dispatch(bus, _intent({**params, "confirmed": "true"}))
    assert "new orders" not in str(gated.rejection)
    assert "upstream MarketData is missing" in str(confirmed.rejection)


def test_invalid_stage_and_missing_bus_are_explained() -> None:
    graph = _source_graph()
    invalid = _dispatch(
        _bound_bus(graph),
        _intent({"run_id": "source", "stage": "unknown", "confirmed": "true"}),
    )
    no_bus = dispatch_intent(
        graph,
        _intent({"run_id": "source", "stage": "provider", "confirmed": "true"}),
    )
    assert invalid.rejection == "invalid resume stage: unknown"
    assert no_bus.rejection == "resume dispatch requires bus context"


def _source_graph() -> InMemoryGraphStore:
    graph = InMemoryGraphStore()
    place_run_request(graph, run_id="source", tickers=("AAPL",))
    return graph


def _bound_bus(graph: InMemoryGraphStore) -> InProcessBus:
    bus = InProcessBus()
    bind_resume_run(bus, graph)
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


def _intent(parameters: dict[str, str]) -> TypedIntent:
    return TypedIntent(
        family="resume",
        parameters=parameters,
        requires_confirmation=True,
        provenance=Provenance(run_id="resume-intent", source_agent="operator"),
    )
