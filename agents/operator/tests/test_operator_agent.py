"""Operator agent tests.

Agent: operator
Role: verify bounded LLM intent parsing, explanations, and graph ledger writes.
External I/O: none.
"""

from __future__ import annotations

import json

from agents.operator import OperatorAgent
from contracts.operator import CommandResult, ExplainRequest, HumanCommand
from kernel import AgentMessage, FakeLLMClient, InMemoryGraphStore, InProcessBus


def test_interpret_maps_all_ten_families_with_confirmation_policy() -> None:
    """OPR-IN-01 / OPR-OUT-01 / OPR-OUT-06 / OPR-OUT-07: all families parsed;
    audit+intent nodes written."""
    graph = InMemoryGraphStore()
    bus = _bound_bus(graph, _family_llm())
    expected = {
        "status": False,
        "explain": False,
        "approve": True,
        "reject": True,
        "modify": True,
        "run": True,
        "mode": True,
        "stage": True,
        "pause": False,
        "resume": False,
    }
    for family, requires_confirmation in expected.items():
        result = _interpret(bus, f"{family} please")
        assert result.outcome == "intent"
        assert result.intent is not None
        assert result.intent.family == family
        assert result.intent.requires_confirmation is requires_confirmation
    assert _node_count(graph, "CommandAudit") == 10
    assert _node_count(graph, "Intent") == 10
    assert _node_count(graph, "LLMCall") == 10


def test_interpret_malformed_refused_and_clarification_paths() -> None:
    """OPR-NEV-05 / OPR-OUT-05 / OPR-OUT-06: malformed/refused/clarification paths;
    no Intent node on refusal."""
    graph = InMemoryGraphStore()
    bus = _bound_bus(
        graph,
        FakeLLMClient(
            {
                "broken": "not json",
                "refuse": _raw("refused", reason="unsafe"),
                "clarify": _raw("needs_clarification", reason="which run?"),
            }
        ),
    )
    assert _interpret(bus, "broken").outcome == "refused"
    assert _interpret(bus, "refuse").message.summary == "unsafe"
    assert _interpret(bus, "clarify").outcome == "needs_clarification"
    assert _node_count(graph, "CommandAudit") == 3
    assert _node_count(graph, "Intent") == 0


def test_interpret_invalid_intent_family_is_refused() -> None:
    """OPR-NEV-01 / OPR-FAIL-02: unknown family → refused; no Intent node written."""
    graph = InMemoryGraphStore()
    bus = _bound_bus(
        graph,
        FakeLLMClient({"bogus": _raw("intent", family="bogus", reason="bad family")}),
    )
    result = _interpret(bus, "bogus")
    assert result.outcome == "refused"
    assert _node_count(graph, "Intent") == 0


def test_interpret_llm_exception_returns_refusal() -> None:
    """OPR-FAIL-01 / OPR-IN-03: LLM exception → refused; fault captured;
    never raises to bus."""
    graph = InMemoryGraphStore()
    bus = _bound_bus(graph, _RaisingLLM({}))
    result = _interpret(bus, "run")
    assert result.outcome == "refused"
    assert "could not parse" in result.message.summary


def test_explain_returns_text_and_writes_audit_and_llm_call() -> None:
    """OPR-IN-02 / OPR-OUT-04 / OPR-OUT-06 / OPR-STA-03: explain → Explanation +
    CommandAudit + LLMCall nodes."""
    graph = InMemoryGraphStore()
    graph.merge_node("Recommendation", "rec:aapl", {"ticker": "AAPL"})
    bus = _bound_bus(graph, FakeLLMClient({"AAPL": "AAPL was recommended."}))
    response = bus.request(
        AgentMessage(
            sender="dashboard",
            recipient="operator",
            message_type="request",
            capability="explain",
            payload=ExplainRequest(subject="why AAPL").model_dump(mode="json"),
        )
    )
    assert response.payload["summary"] == "AAPL was recommended."
    assert _node_count(graph, "CommandAudit") == 1
    assert _node_count(graph, "LLMCall") == 1


def test_ledger_is_idempotent_for_same_command() -> None:
    """OPR-IDM-03: same (actor, channel, text) → same correlation_id;
    single node set."""
    graph = InMemoryGraphStore()
    bus = _bound_bus(graph, _family_llm())
    _interpret(bus, "run please")
    _interpret(bus, "run please")
    assert _node_count(graph, "CommandAudit") == 1
    assert _node_count(graph, "Intent") == 1
    assert _node_count(graph, "LLMCall") == 1


def test_operator_boundary_claims_graph_labels_once() -> None:
    """OPR-IDN-02: operator exclusively owns CommandAudit, Intent, LLMCall
    (single-writer rule)."""
    from contracts.operator import CONTRACT

    assert CONTRACT.owns_graph == ("CommandAudit", "Intent", "LLMCall")


def _bound_bus(graph: InMemoryGraphStore, llm: FakeLLMClient) -> InProcessBus:
    bus = InProcessBus()
    OperatorAgent(bus, graph=graph, llm=llm).bind()
    return bus


def _interpret(bus: InProcessBus, text: str) -> CommandResult:
    response = bus.request(
        AgentMessage(
            sender="dashboard",
            recipient="operator",
            message_type="request",
            capability="interpret",
            payload=HumanCommand(
                text=text, actor="admin", channel="dashboard"
            ).model_dump(mode="json"),
        )
    )
    return CommandResult.model_validate(response.payload)


def _family_llm() -> FakeLLMClient:
    return FakeLLMClient(
        {family: _raw("intent", family=family) for family in _FAMILIES}
    )


def _raw(outcome: str, *, family: str = "status", reason: str = "") -> str:
    payload = {"outcome": outcome, "family": family, "parameters": {}}
    if reason:
        payload["reason"] = reason
    return json.dumps(payload)


def _node_count(graph: InMemoryGraphStore, label: str) -> int:
    return len(graph.list_nodes(label))


_FAMILIES = (
    "status",
    "explain",
    "approve",
    "reject",
    "modify",
    "run",
    "mode",
    "stage",
    "pause",
    "resume",
)


class _RaisingLLM(FakeLLMClient):
    def complete(
        self, *, system: str, user: str, tool_schema: dict[str, object]
    ) -> str:
        raise RuntimeError("model down")
