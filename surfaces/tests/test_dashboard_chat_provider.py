"""Dashboard selected-provider binding tests.

Agent: surfaces
Role: prove the chat requires exactly its selected vendor's credentials.
External I/O: none; SDK and graph are fake.
"""

import importlib
from types import SimpleNamespace

import pytest

from kernel import InMemoryGraphStore
from kernel.llm_anthropic import ConfigurationError as AnthropicConfigurationError
from kernel.llm_openai import ConfigurationError as OpenAIConfigurationError
from surfaces.dashboard import chat_binding

TEST_CREDENTIAL = "fixture-value"


@pytest.mark.parametrize(
    "error_type",
    [AnthropicConfigurationError, OpenAIConfigurationError],
)
def test_each_vendor_configuration_error_disconnects(
    monkeypatch: pytest.MonkeyPatch, error_type: type[Exception]
) -> None:
    """SRF-DEP-03: both vendors' configuration refusals leave chat disconnected."""
    monkeypatch.setenv("OPERATOR_LLM_PROVIDER", "openai")

    def refuse(*args: object, **kwargs: object) -> object:
        raise error_type("fixture configuration refusal")

    monkeypatch.setattr(chat_binding, "build_operator_llm", refuse)
    assert (
        chat_binding.bind_dashboard_chat(
            InMemoryGraphStore(),
            {"POSTGRES_DSN": "fixture", "OPENAI_API_KEY": TEST_CREDENTIAL},
        )
        is None
    )


def test_b5_chat_binds_only_with_selected_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """SRF-DEP-03 / SRF-IN-03: OpenAI-only credentials bind OpenAI chat."""
    monkeypatch.setenv("OPERATOR_LLM_PROVIDER", "openai")
    imports: list[str] = []

    def fake_import(name: str) -> object:
        imports.append(name)
        return SimpleNamespace(OpenAI=lambda **kwargs: object())

    monkeypatch.setattr(importlib, "import_module", fake_import)
    monkeypatch.setattr(chat_binding, "paper_context", lambda **kwargs: kwargs)
    graph = InMemoryGraphStore()
    bound = chat_binding.bind_dashboard_chat(
        graph, {"POSTGRES_DSN": "fixture", "OPENAI_API_KEY": TEST_CREDENTIAL}
    )
    assert bound is not None
    assert imports == ["openai"]
    refused_calls: list[object] = []

    def must_not_construct(*args: object, **kwargs: object) -> object:
        refused_calls.append(args)
        raise OpenAIConfigurationError("fixture missing-key refusal")

    monkeypatch.setattr(chat_binding, "build_operator_llm", must_not_construct)
    assert (
        chat_binding.bind_dashboard_chat(
            graph, {"POSTGRES_DSN": "fixture", "ANTHROPIC_API_KEY": TEST_CREDENTIAL}
        )
        is None
    )
    assert refused_calls == []
    monkeypatch.setenv("OPERATOR_LLM_PROVIDER", "opnai")
    assert (
        chat_binding.bind_dashboard_chat(
            graph, {"POSTGRES_DSN": "fixture", "OPENAI_API_KEY": TEST_CREDENTIAL}
        )
        is None
    )
