"""Failed operator requests are audited and answered through the bus.

Agent: operator
Role: prove request fault ownership, audit ordering, and plain refusal reasons.
External I/O: none; synthetic clients and in-memory graph and bus.
"""

from __future__ import annotations

import pytest

from agents.operator import agent as agent_module
from agents.operator.tests.cutoff_helpers import CompletionStub
from agents.operator.tests.failed_request_helpers import (
    assert_audit,
    build_agent,
    command,
)
from contracts.operator import ExplainRequest
from kernel import AgentMessage, CollectingFaultSink


def test_s265_c1_failed_explain_is_audited_and_answers_through_bus() -> None:
    """OPR-FAIL-01 / OPR-OUT-06 / OPR-IN-03: one agent fault, no bus error."""
    llm = CompletionStub(failed=True)
    _agent, graph, bus, sink = build_agent(llm)
    response = bus.request(
        AgentMessage(
            sender="dashboard",
            recipient="operator",
            message_type="request",
            capability="explain",
            payload=ExplainRequest(subject="explain this run").model_dump(mode="json"),
        )
    )
    assert response.message_type == "response"
    assert response.payload["summary"] == (
        "The request to the language model failed, so there is no answer. "
        "fixture request timed out"
    )
    assert_audit(graph, "explain")
    assert len(sink.faults) == 1
    fault = sink.faults[0]
    assert fault.source_agent == "operator"
    assert fault.source_module == "agents.operator.agent"
    assert fault.capability == "explain"
    assert fault.error_type == "TimeoutError"
    assert fault.message == "fixture request timed out"
    assert isinstance(bus.sink, CollectingFaultSink)
    assert not bus.sink.faults
    assert len(llm.requests) == 1


def test_s265_c2_failed_interpret_is_audited_and_says_why() -> None:
    """OPR-FAIL-01 / OPR-OUT-06 / OPR-OUT-05: failed parse is an audited refusal."""
    llm = CompletionStub(failed=True)
    agent, graph, bus, sink = build_agent(llm)
    result = agent._interpret(command())
    assert result.outcome == "refused"
    assert result.intent is None
    assert result.message.summary == (
        "The request to the language model failed, so there is no answer. "
        "fixture request timed out"
    )
    assert_audit(graph, "refused")
    assert len(sink.faults) == 1
    fault = sink.faults[0]
    assert fault.capability == "interpret"
    assert fault.source_agent == "operator"
    assert fault.source_module == "agents.operator.agent"
    assert fault.error_type == "TimeoutError"
    assert isinstance(bus.sink, CollectingFaultSink)
    assert not bus.sink.faults
    assert len(llm.requests) == 1


def test_s265_c3_failed_approve_never_enters_explicit_grammar(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """OPR-FAIL-01: failed approval refuses without applying the command grammar."""

    def forbidden(text: str, data: dict[str, object]) -> dict[str, object]:
        pytest.fail("failed request reached the explicit command grammar")

    monkeypatch.setattr(agent_module, "normalize_explicit_intent", forbidden)
    agent, graph, _bus, sink = build_agent(CompletionStub(failed=True))
    result = agent._interpret(command("approve flag-12"))
    assert result.outcome == "refused"
    assert result.intent is None
    assert result.message.summary == (
        "The request to the language model failed, so there is no answer. "
        "fixture request timed out"
    )
    assert_audit(graph, "refused")
    assert len(sink.faults) == 1
    assert sink.faults[0].capability == "interpret"
