"""LLM adapter key-containment and operator-dependency tests.

Agent: kernel
Role: prove vendor keys stay within the adapter and operator calls stay Anthropic-only.
External I/O: none; Anthropic SDK calls are faked.
"""

from __future__ import annotations

import logging
from types import SimpleNamespace
from typing import TYPE_CHECKING

import kernel.llm_anthropic as anthropic_adapter
from agents.deliberator.agent import DeliberatorAgent
from agents.deliberator.settings import DeliberatorSettings
from agents.operator.agent import OperatorAgent
from contracts.deliberator import DebateProposition, DebateTurnRequest
from contracts.operator import HumanCommand
from kernel import InMemoryGraphStore, InProcessBus
from kernel.llm_anthropic import AnthropicLLMClient, OperatorAnthropicLLMClient

if TYPE_CHECKING:
    import pytest


_SENTINEL = "S222-ANTHROPIC-KEY-SENTINEL"


class _FakeMessages:
    def create(self, **kwargs: object) -> object:
        if "tools" in kwargs:
            return SimpleNamespace(
                content=[
                    SimpleNamespace(
                        type="tool_use",
                        input={
                            "outcome": "intent",
                            "family": "status",
                            "parameters": {},
                        },
                    )
                ],
                usage=SimpleNamespace(
                    input_tokens=1,
                    output_tokens=1,
                    cache_read_input_tokens=0,
                    cache_creation_input_tokens=0,
                ),
            )
        return SimpleNamespace(
            content=[SimpleNamespace(type="text", text="safe deliberation")],
            stop_reason="end_turn",
            usage=SimpleNamespace(
                input_tokens=1,
                output_tokens=1,
                cache_read_input_tokens=0,
                cache_creation_input_tokens=0,
            ),
        )


class _FakeAnthropic:
    def __init__(self, *, api_key: str) -> None:
        assert api_key == _SENTINEL
        self.messages = _FakeMessages()


def _install_anthropic_fake(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    imports: list[str] = []

    def fake_import(name: str) -> object:
        imports.append(name)
        return SimpleNamespace(Anthropic=_FakeAnthropic)

    monkeypatch.setattr(anthropic_adapter.importlib, "import_module", fake_import)
    return imports


def test_anthropic_key_never_escapes_deliberator_or_operator(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """DLIB-SEC-02 / OPR-SEC-01: key absent from results, graph, and logs."""
    caplog.set_level(logging.DEBUG)
    _install_anthropic_fake(monkeypatch)
    deliberator_graph = InMemoryGraphStore()
    deliberator = DeliberatorAgent(
        InProcessBus(),
        graph=deliberator_graph,
        llm=AnthropicLLMClient(api_key=_SENTINEL),
        settings=DeliberatorSettings(role="proponent"),
    )
    reply = deliberator.debate_turn(
        DebateTurnRequest(
            request_id="s222-security-deliberator",
            proposition=DebateProposition(decision="buy AAPL", context="bounded"),
            role="defender",
            round_number=1,
        )
    )
    operator_graph = InMemoryGraphStore()
    operator = OperatorAgent(
        InProcessBus(),
        graph=operator_graph,
        llm=OperatorAnthropicLLMClient(api_key=_SENTINEL),
    )
    result = operator._interpret(
        HumanCommand(text="status", actor="admin", channel="dashboard")
    )

    evidence = "\n".join(
        (
            repr(reply),
            repr(result),
            repr(deliberator_graph.list_nodes("LLMCall")),
            repr(operator_graph.list_nodes("LLMCall")),
            repr(operator_graph.list_nodes("CommandAudit")),
            repr(operator.__dict__),
            caplog.text,
        )
    )
    assert _SENTINEL not in evidence


def test_operator_adapter_imports_anthropic_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """OPR-DEP-01: the operator's sole vendor dependency is Anthropic."""
    imports = _install_anthropic_fake(monkeypatch)
    client = OperatorAnthropicLLMClient(api_key=_SENTINEL)

    client.complete(system="system", user="status", tool_schema={})

    assert imports == ["anthropic"]
