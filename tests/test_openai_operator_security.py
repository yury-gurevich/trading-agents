"""OpenAI operator vendor key containment.

Agent: kernel
Role: prove keys reach only the selected lazy SDK constructor.
External I/O: none; SDK and graph are fake.
"""

import logging
from types import SimpleNamespace

import pytest
from tests.test_llm_adapter_ownership import VENDOR_ADAPTER_CLASSES

from agents.operator.agent import OperatorAgent
from agents.operator.settings import OperatorSettings
from contracts.operator import HumanCommand
from kernel import InMemoryGraphStore, InProcessBus, llm_openai_operator
from kernel.llm_factory import build_operator_llm


def test_b6_openai_key_never_escapes_operator(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """OPR-SEC-01 / OPR-DEP-01: OpenAI key absent from results, graph and logs."""
    sentinel = "S262-OPENAI-KEY-SENTINEL"
    imports: list[str] = []

    def constructor(*, api_key: str) -> object:
        assert api_key == sentinel
        response = SimpleNamespace(
            status="completed",
            output=[
                SimpleNamespace(
                    type="function_call",
                    arguments='{"outcome":"intent","family":"status","parameters":{}}',
                )
            ],
        )
        return SimpleNamespace(
            responses=SimpleNamespace(create=lambda **kwargs: response)
        )

    def fake_import(name: str) -> object:
        imports.append(name)
        return SimpleNamespace(OpenAI=constructor)

    caplog.set_level(logging.DEBUG)
    monkeypatch.setenv("OPERATOR_LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPERATOR_MODEL", "")
    monkeypatch.setenv("OPERATOR_EFFORT", "")
    monkeypatch.setattr(llm_openai_operator.importlib, "import_module", fake_import)
    client = build_operator_llm(
        "openai", api_key=sentinel, model="gpt-5.5", max_tokens=4096, effort="max"
    )
    graph = InMemoryGraphStore()
    operator = OperatorAgent(
        InProcessBus(),
        graph=graph,
        llm=client,
        settings=OperatorSettings(llm_provider="openai"),
    )
    result = operator._interpret(
        HumanCommand(text="status", actor="admin", channel="dashboard")
    )
    assert result.outcome == "intent"
    evidence = (
        repr(
            (
                result,
                operator.__dict__,
                graph.list_nodes("LLMCall"),
                graph.list_nodes("CommandAudit"),
            )
        )
        + caplog.text
    )
    assert sentinel not in evidence
    assert imports == ["openai"]
    assert "OperatorOpenAILLMClient" in VENDOR_ADAPTER_CLASSES
