"""Operator model resolution and ledger attribution.

Agent: operator
Role: prove both model readers record the provider-resolved model.
External I/O: none; in-memory graph and fake LLM.
"""

import pytest

from agents.operator.agent import OperatorAgent
from agents.operator.settings import OperatorSettings
from contracts.operator import ExplainRequest, HumanCommand
from kernel import FakeLLMClient, InMemoryGraphStore, InProcessBus


def test_b1_model_follows_provider_and_override(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """OPR-DEP-01 / OPR-STA-03: default, declared and explicit models resolve."""
    monkeypatch.delenv("OPERATOR_MODEL", raising=False)
    monkeypatch.delenv("OPERATOR_LLM_PROVIDER", raising=False)
    assert OperatorSettings(_env_file=None).resolved_model == "claude-opus-5"
    monkeypatch.setenv("OPERATOR_LLM_PROVIDER", "openai")
    settings = OperatorSettings(_env_file=None)
    assert settings.model == ""
    assert settings.resolved_model == "gpt-5.5"
    assert (
        OperatorSettings(_env_file=None, model="explicit").resolved_model == "explicit"
    )
    graph = InMemoryGraphStore()
    agent = OperatorAgent(
        InProcessBus(), graph=graph, llm=FakeLLMClient({}), settings=settings
    )
    agent._interpret(HumanCommand(text="status", actor="admin", channel="dashboard"))
    agent._explain(ExplainRequest(subject="status"))
    calls = graph.list_nodes("LLMCall")
    assert len(calls) == 2
    assert all(call.props["model"] == "gpt-5.5" for call in calls)


def test_container_keeps_fake_client_with_declared_vendor() -> None:
    """OPR-SEC-01 / OPR-DEP-01: declaring a vendor never builds a container client."""
    agent = OperatorAgent(
        InProcessBus(),
        graph=InMemoryGraphStore(),
        settings=OperatorSettings(llm_provider="openai"),
    )
    assert isinstance(agent._llm, FakeLLMClient)
