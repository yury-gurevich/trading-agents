"""Operator Anthropic adapter tests.

Agent: operator
Role: verify construction failures and tool-use extraction without network I/O.
External I/O: none.
"""

from __future__ import annotations

import importlib
from types import SimpleNamespace

import pytest

from agents.operator.llm_anthropic import (
    AnthropicLLMClient,
    ConfigurationError,
    _tool_input,
)


def test_anthropic_client_requires_api_key() -> None:
    with pytest.raises(ConfigurationError, match="ANTHROPIC_API_KEY"):
        AnthropicLLMClient(api_key="")


def test_anthropic_client_requires_installed_package(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def missing(_name: str) -> object:
        raise ModuleNotFoundError("anthropic")

    monkeypatch.setattr(importlib, "import_module", missing)
    with pytest.raises(ConfigurationError, match="not installed"):
        AnthropicLLMClient(api_key="key")  # pragma: allowlist secret


def test_anthropic_complete_extracts_tool_input(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(importlib, "import_module", lambda _name: _FakeAnthropicModule)
    client = AnthropicLLMClient(api_key="key")  # pragma: allowlist secret
    raw = client.complete(system="s", user="u", tool_schema={"type": "object"})
    assert "status" in raw


def test_tool_input_fallbacks() -> None:
    text_first = SimpleNamespace(
        content=[
            SimpleNamespace(type="text", input={"ignored": True}),
            SimpleNamespace(type="tool_use", input={"outcome": "intent"}),
        ]
    )
    assert _tool_input(text_first) == {"outcome": "intent"}
    assert _tool_input(SimpleNamespace(content=[])) == {
        "outcome": "refused",
        "reason": "model returned no tool result",
    }
    response = SimpleNamespace(
        content=[SimpleNamespace(type="tool_use", input=("not", "dict"))]
    )
    assert _tool_input(response) == {}


class _FakeMessages:
    def create(self, **_kwargs: object) -> object:
        return SimpleNamespace(
            content=[
                SimpleNamespace(
                    type="tool_use",
                    input={"outcome": "intent", "family": "status"},
                )
            ]
        )


class _FakeAnthropic:
    def __init__(self, *, api_key: str) -> None:
        self.api_key = api_key
        self.messages = _FakeMessages()


_FakeAnthropicModule = SimpleNamespace(Anthropic=_FakeAnthropic)
