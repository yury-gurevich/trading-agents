"""Operator cut-off behavior, audit, grammar, and failed-request regressions.

Agent: operator
Role: prove the two call sites distinguish cut-off replies from failed requests.
External I/O: none; synthetic completions and in-memory graph.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from agents.operator.agent import OperatorAgent
from agents.operator.domain.result import CUT_OFF_REPLY, parse_json
from agents.operator.settings import OperatorSettings
from agents.operator.tests.cutoff_helpers import CompletionStub, assert_vendor_row
from contracts.operator import ExplainRequest, HumanCommand
from kernel import CollectingFaultSink, InMemoryGraphStore, InProcessBus

if TYPE_CHECKING:
    from kernel.errors import AgentFault


def _agent(llm: CompletionStub) -> tuple[OperatorAgent, InMemoryGraphStore]:
    graph = InMemoryGraphStore()
    agent = OperatorAgent(
        InProcessBus(),
        graph=graph,
        llm=llm,
        settings=OperatorSettings(_env_file=None, llm_provider="anthropic"),
    )
    return agent, graph


def _audit(graph: InMemoryGraphStore, stop: str, outcome: str) -> None:
    rows, audits = graph.list_nodes("LLMCall"), graph.list_nodes("CommandAudit")
    assert len(rows) == len(audits) == 1
    assert_vendor_row(rows[0], stop)
    assert audits[0].props["outcome"] == outcome
    assert (
        tuple(graph.descendants(audits[0], max_depth=1, edge_types={"PRODUCED_BY"}))
        == rows
    )


def _faults(agent: OperatorAgent) -> list[AgentFault]:
    assert isinstance(agent.sink, CollectingFaultSink)
    return agent.sink.faults


@pytest.mark.parametrize("stop", ["max_tokens", "max_output_tokens"])
def test_c1_cutoff_explain_audits_before_returning_the_sentence(stop: str) -> None:
    """OPR-FAIL-04 / OPR-OUT-06 / OPR-STA-03: cut-off explain audits without fault."""
    llm = CompletionStub(stop, stopped=True)
    agent, graph = _agent(llm)
    reply = agent._explain(ExplainRequest(subject="explain this run"))
    assert reply.summary == CUT_OFF_REPLY
    _audit(graph, stop, "explain")
    assert not graph.list_nodes("Intent")
    assert not _faults(agent)
    assert len(llm.requests) == 1


@pytest.mark.parametrize("stop", ["max_tokens", "max_output_tokens"])
def test_c2_cutoff_interpret_refuses_with_reason_and_linked_audit(stop: str) -> None:
    """OPR-FAIL-04 / OPR-OUT-05 / OPR-OBS-03: cut-off parse refuses, with no intent."""
    agent, graph = _agent(CompletionStub(stop, stopped=True))
    result = agent._interpret(
        HumanCommand(
            text="What happened in this run?", actor="operator", channel="dashboard"
        )
    )
    assert parse_json(None) == {"outcome": "refused", "reason": CUT_OFF_REPLY}
    assert result.outcome == "refused"
    assert result.intent is None
    assert result.message.summary == CUT_OFF_REPLY
    _audit(graph, stop, "refused")
    assert not graph.list_nodes("Intent")
    assert not _faults(agent)


@pytest.mark.parametrize("stop", ["max_tokens", "max_output_tokens"])
def test_c3_explicit_approve_keeps_grammar_after_cutoff(stop: str) -> None:
    """OPR-FAIL-04: explicit approval survives cut-off and still needs confirmation."""
    agent, graph = _agent(CompletionStub(stop, stopped=True))
    result = agent._interpret(
        HumanCommand(text="approve flag-12", actor="operator", channel="dashboard")
    )
    assert result.outcome == "intent"
    assert result.intent is not None
    assert result.intent.family == "approve"
    assert result.intent.parameters == {"target": "flag-12"}
    assert result.intent.requires_confirmation is True
    assert len(graph.list_nodes("Intent")) == 1
    _audit(graph, stop, "intent")
    assert not _faults(agent)


@pytest.mark.parametrize(
    ("capability", "stop"), [("explain", "completed"), ("interpret", "tool_use")]
)
def test_c4_finished_call_records_the_clients_stop_reason(
    capability: str, stop: str
) -> None:
    """OPR-STA-03: both agent call sites retain a finished reply's vendor metadata."""
    llm = CompletionStub(stop, json.dumps({"outcome": "intent", "family": "status"}))
    agent, graph = _agent(llm)
    if capability == "explain":
        reply = agent._explain(ExplainRequest(subject="question"))
        assert reply.summary == llm.response
    else:
        result = agent._interpret(
            HumanCommand(text="status", actor="operator", channel="dashboard")
        )
        assert result.outcome == "intent"
    _audit(graph, stop, "explain" if capability == "explain" else "intent")
    assert not _faults(agent)


def test_c5_failed_interpret_says_why_and_writes_linked_audit() -> None:
    """OPR-FAIL-01: time-outs say why, with one fault and a linked refusal audit."""
    agent, graph = _agent(CompletionStub(failed=True))
    result = agent._interpret(
        HumanCommand(text="question", actor="operator", channel="dashboard")
    )
    assert result.outcome == "refused"
    assert result.message.summary == (
        "The request to the language model failed, so there is no answer. "
        "fixture request timed out"
    )
    assert len(_faults(agent)) == 1
    assert _faults(agent)[0].error_type == "TimeoutError"
    rows = graph.list_nodes("LLMCall")
    assert len(rows) == 1
    assert rows[0].props["stop_reason"] == "unknown"
    assert rows[0].props.get("token_source") == "estimated"
    (audit,) = graph.list_nodes("CommandAudit")
    assert audit.props["outcome"] == "refused"
    assert (
        tuple(graph.descendants(audit, max_depth=1, edge_types={"PRODUCED_BY"})) == rows
    )
    assert not graph.list_nodes("Intent")


def test_c6_cutoff_sentence_is_pinned_letter_for_letter() -> None:
    """OPR-FAIL-04: the cut-off text names no vendor, model, number or token."""
    assert CUT_OFF_REPLY == (
        "The model's reply was cut off at its output limit before it finished, "
        "so there is no answer. Ask again, or ask something narrower."
    )
    assert not any(
        word in CUT_OFF_REPLY.lower()
        for word in ("openai", "anthropic", "gpt", "claude", "token")
    )
    assert not any(character.isdigit() for character in CUT_OFF_REPLY)
