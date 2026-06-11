"""P5 operator-to-supervisor exit tests.

Agent: supervisor
Role: prove OperatorAgent intents flow through SupervisorAgent safely.
External I/O: none.
"""

from __future__ import annotations

import json

from agents.operator import OperatorAgent
from agents.supervisor import SupervisorAgent
from contracts.operator import CommandResult, HumanCommand
from contracts.supervisor import DispatchResult
from kernel import AgentMessage, FakeLLMClient, InMemoryGraphStore, InProcessBus


def test_p5_operator_to_supervisor_run_intent() -> None:
    graph = InMemoryGraphStore()
    bus = _bound_bus(graph, _run_llm())
    command = _interpret(bus, "run the daily scan", "dashboard")
    assert command.outcome == "intent"
    assert command.intent is not None
    result = _dispatch(bus, command.intent)
    assert result.accepted is True
    assert result.routed_to == "orchestration.execute_run"
    assert _node_count(graph, "CommandAudit") == 1
    assert _node_count(graph, "Message") == 1


def test_p5_hard_no_blocks_unconditionally() -> None:
    graph = InMemoryGraphStore()
    bus = _bound_bus(graph, _run_llm())
    command = _interpret(bus, "run live now", "dashboard")
    assert command.intent is not None
    result = _dispatch(bus, command.intent)
    assert result.accepted is False
    assert "live-stage" in str(result.rejection)
    assert _node_count(graph, "Message") == 0


def test_p5_policy_parity_dashboard_vs_mcp() -> None:
    graph = InMemoryGraphStore()
    bus = _bound_bus(graph, _run_llm())
    dashboard = _interpret(bus, "run the daily scan", "dashboard")
    mcp = _interpret(bus, "run the daily scan", "mcp")
    assert dashboard.intent is not None
    assert mcp.intent is not None
    assert dashboard.intent.family == mcp.intent.family
    assert dashboard.intent.requires_confirmation == mcp.intent.requires_confirmation
    dash_result = _dispatch(bus, dashboard.intent)
    mcp_result = _dispatch(bus, mcp.intent)
    assert (dash_result.accepted, dash_result.routed_to) == (
        mcp_result.accepted,
        mcp_result.routed_to,
    )


def _bound_bus(graph: InMemoryGraphStore, llm: FakeLLMClient) -> InProcessBus:
    bus = InProcessBus()
    OperatorAgent(bus, graph=graph, llm=llm).bind()
    SupervisorAgent(bus, graph=graph).bind()
    return bus


def _interpret(bus: InProcessBus, text: str, channel: str) -> CommandResult:
    response = bus.request(
        AgentMessage(
            sender=channel,
            recipient="operator",
            message_type="request",
            capability="interpret",
            payload=HumanCommand(
                text=text,
                actor="admin",
                channel=channel,  # type: ignore[arg-type]
            ).model_dump(mode="json"),
        )
    )
    return CommandResult.model_validate(response.payload)


def _dispatch(bus: InProcessBus, intent: object) -> DispatchResult:
    response = bus.request(
        AgentMessage(
            sender="operator",
            recipient="supervisor",
            message_type="request",
            capability="dispatch_intent",
            payload=intent.model_dump(mode="json"),  # type: ignore[attr-defined]
        )
    )
    return DispatchResult.model_validate(response.payload)


def _run_llm() -> FakeLLMClient:
    return FakeLLMClient(
        {
            "live": json.dumps(
                {
                    "outcome": "intent",
                    "family": "run",
                    "parameters": {"stage": "live", "confirmed": "true"},
                }
            ),
            "run": json.dumps(
                {
                    "outcome": "intent",
                    "family": "run",
                    "parameters": {"stage": "paper", "confirmed": "true"},
                }
            ),
        }
    )


def _node_count(graph: InMemoryGraphStore, label: str) -> int:
    return len(graph.list_nodes(label))
