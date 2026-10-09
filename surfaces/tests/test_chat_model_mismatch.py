"""Dashboard operator model and effort binding guards.

Agent: surfaces
Role: prove mismatch disconnection and provider-resolved settings.
External I/O: none; fake SDK constructors and in-memory graph only.
"""

import importlib
from types import SimpleNamespace

import pytest

from kernel import InMemoryGraphStore
from surfaces.dashboard import chat_binding


def test_c1_mismatch_disconnects_with_reason(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """SRF-DEP-03: a cross-vendor model disconnects chat and names why on stderr."""
    monkeypatch.setenv("OPERATOR_LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPERATOR_MODEL", "claude-opus-5")
    monkeypatch.setenv("OPERATOR_EFFORT", "max")
    imports: list[str] = []

    def fake_import(name: str) -> object:
        imports.append(name)
        return SimpleNamespace(OpenAI=lambda **kwargs: object())

    monkeypatch.setattr(importlib, "import_module", fake_import)
    monkeypatch.setattr(chat_binding, "paper_context", lambda **kwargs: kwargs)
    result = chat_binding.bind_dashboard_chat(
        InMemoryGraphStore(),
        {
            "POSTGRES_DSN": "fixture",
            "OPENAI_API_KEY": "fixture-value",  # pragma: allowlist secret
        },
    )
    assert result is None
    captured = capsys.readouterr()
    assert captured.out == ""
    assert len(captured.err.splitlines()) == 1
    assert captured.err.startswith("dashboard: operator chat not connected:")
    assert all(
        word in captured.err for word in ("claude-opus-5", "anthropic", "openai")
    )
    assert imports == []


@pytest.mark.parametrize(
    ("provider", "model", "effort", "key"),
    [
        ("openai", "gpt-5.5", "xhigh", "OPENAI_API_KEY"),
        ("anthropic", "claude-opus-5", "max", "ANTHROPIC_API_KEY"),
    ],
)
def test_c2_binding_passes_resolved_settings(
    monkeypatch: pytest.MonkeyPatch, provider: str, model: str, effort: str, key: str
) -> None:
    """SRF-DEP-03 / OPR-DEP-01: binding passes provider-resolved model and effort."""
    monkeypatch.setenv("OPERATOR_LLM_PROVIDER", provider)
    monkeypatch.setenv("OPERATOR_MODEL", "")
    monkeypatch.setenv("OPERATOR_EFFORT", "")
    calls: list[tuple[str, dict[str, object]]] = []
    sentinel = object()
    context = object()
    contexts: list[dict[str, object]] = []

    def build(selected: str, **kwargs: object) -> object:
        calls.append((selected, kwargs))
        return sentinel

    def compose(**kwargs: object) -> object:
        contexts.append(kwargs)
        return context

    monkeypatch.setattr(chat_binding, "build_operator_llm", build)
    monkeypatch.setattr(chat_binding, "paper_context", compose)
    graph = InMemoryGraphStore()
    assert (
        chat_binding.bind_dashboard_chat(
            graph,
            {
                "POSTGRES_DSN": "fixture",
                key: "fixture-value",
            },  # pragma: allowlist secret
        )
        is context
    )
    assert contexts == [{"graph": graph, "llm": sentinel}]
    assert calls == [
        (
            provider,
            {
                "api_key": "fixture-value",  # pragma: allowlist secret
                "model": model,
                "max_tokens": 4096,
                "effort": effort,
            },
        )
    ]
