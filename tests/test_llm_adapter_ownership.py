"""Kernel LLM adapter ownership boundary tests.

Agent: kernel
Role: prevent vendor adapter implementations from returning to agents.
External I/O: reads tracked Python source paths.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from kernel import llm_factory

REPOSITORY_ROOT = Path(__file__).parents[1]
VENDOR_ADAPTER_CLASSES = frozenset(
    {"AnthropicLLMClient", "OpenAILLMClient", "OperatorAnthropicLLMClient"}
)


def test_vendor_adapter_implementations_live_only_in_kernel() -> None:
    """S222 A1: vendor adapters and their factory are kernel-owned."""
    offenders = sorted(
        path.relative_to(REPOSITORY_ROOT).as_posix()
        for path in (REPOSITORY_ROOT / "agents").rglob("*.py")
        if path.name.startswith("llm_")
        or any(
            isinstance(node, ast.ClassDef) and node.name in VENDOR_ADAPTER_CLASSES
            for node in ast.parse(path.read_text(encoding="utf-8")).body
        )
    )

    assert not offenders, (
        "vendor adapter implementations outside kernel:\n" + "\n".join(offenders)
    )


def test_surfaces_do_not_import_agent_llm_adapters() -> None:
    """S222 A6: surfaces import vendor clients only from kernel."""
    offenders = sorted(
        path.relative_to(REPOSITORY_ROOT).as_posix()
        for path in (REPOSITORY_ROOT / "surfaces").rglob("*.py")
        if any(
            isinstance(node, ast.ImportFrom)
            and node.module is not None
            and node.module.startswith("agents.")
            and ".llm_" in node.module
            for node in ast.parse(path.read_text(encoding="utf-8")).body
        )
    )

    assert not offenders, "surfaces importing agent LLM adapters:\n" + "\n".join(
        offenders
    )


def test_selected_provider_failure_never_builds_another_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """S222 A4: provider selection never falls back to a different vendor."""
    calls: list[str] = []

    def broken_anthropic(**_kwargs: object) -> object:
        calls.append("anthropic")
        raise RuntimeError("Anthropic unavailable")

    def unexpected_openai(**_kwargs: object) -> object:
        calls.append("openai")
        return object()

    monkeypatch.setattr(llm_factory, "AnthropicLLMClient", broken_anthropic)
    monkeypatch.setattr(llm_factory, "OpenAILLMClient", unexpected_openai)

    with pytest.raises(RuntimeError, match="Anthropic unavailable"):
        llm_factory.build_llm(
            "anthropic",
            api_key="key",  # pragma: allowlist secret
            model="claude-opus-5",
            max_tokens=16,
            effort="max",
        )

    assert calls == ["anthropic"]
