"""Operator provider defaults and cross-vendor model refusal.

Agent: kernel
Role: prove provider effort resolution and narrow model family checks.
External I/O: none; vendor constructors are fake.
"""

import pytest
from pydantic import ValidationError

from agents.operator.settings import OperatorSettings
from kernel import llm_factory


@pytest.mark.parametrize(
    ("provider", "expected"), [("anthropic", "max"), ("openai", "xhigh")]
)
def test_b1_effort_follows_provider(
    monkeypatch: pytest.MonkeyPatch, provider: str, expected: str
) -> None:
    """OPR-DEP-01: empty effort resolves the provider; explicit values pass through."""
    monkeypatch.setenv("OPERATOR_LLM_PROVIDER", provider)
    monkeypatch.setenv("OPERATOR_MODEL", "")
    monkeypatch.delenv("OPERATOR_EFFORT", raising=False)
    settings = OperatorSettings(_env_file=None)
    assert settings.effort == ""
    assert settings.resolved_effort == expected
    for effort in ("none", "low", "medium", "high", "xhigh", "max"):
        explicit = OperatorSettings(effort=effort, _env_file=None)
        assert explicit.resolved_effort == effort
    monkeypatch.setenv("OPERATOR_EFFORT", "maximum")
    with pytest.raises(ValidationError):
        OperatorSettings(_env_file=None)


def test_b2_unknown_provider_effort() -> None:
    """OPR-DEP-01: a misspelled provider has no default effort."""
    with pytest.raises(llm_factory.UnknownProviderError, match="opnai"):
        llm_factory.default_operator_effort_for("opnai")


@pytest.mark.parametrize(
    ("provider", "model", "owner"),
    [("openai", "claude-opus-5", "anthropic"), ("anthropic", "gpt-5.5", "openai")],
)
def test_b3_mismatched_model_builds_nothing(
    monkeypatch: pytest.MonkeyPatch, provider: str, model: str, owner: str
) -> None:
    """OPR-DEP-01: refuse the other family before constructing either vendor."""
    calls: list[dict[str, object]] = []

    def construct(**kwargs: object) -> object:
        calls.append(kwargs)
        return object()

    monkeypatch.setattr(llm_factory, "OperatorAnthropicLLMClient", construct)
    monkeypatch.setattr(llm_factory, "OperatorOpenAILLMClient", construct)
    with pytest.raises(llm_factory.ModelProviderMismatchError) as error:
        llm_factory.build_operator_llm(
            provider,
            api_key="fixture-value",  # pragma: allowlist secret
            model=model,
            max_tokens=4096,
            effort="max",
        )
    assert all(word in str(error.value) for word in (model, owner, provider))
    assert calls == []


@pytest.mark.parametrize("provider", ["anthropic", "openai"])
@pytest.mark.parametrize("model", ["ft:gpt-5.5:acme", "my-local-model", "explicit"])
def test_b4_unknown_model_family_is_vendors_to_judge(
    monkeypatch: pytest.MonkeyPatch, provider: str, model: str
) -> None:
    """OPR-DEP-01: unrecognized names reach only the selected constructor."""
    calls: list[tuple[str, dict[str, object]]] = []
    sentinel = object()

    def selected(**kwargs: object) -> object:
        calls.append((provider, kwargs))
        return sentinel

    def other(**kwargs: object) -> object:
        calls.append(("other", kwargs))
        return object()

    for vendor, name in (
        ("anthropic", "OperatorAnthropicLLMClient"),
        ("openai", "OperatorOpenAILLMClient"),
    ):
        monkeypatch.setattr(
            llm_factory, name, selected if vendor == provider else other
        )
    assert (
        llm_factory.build_operator_llm(
            provider,
            api_key="fixture-value",  # pragma: allowlist secret
            model=model,
            max_tokens=4096,
            effort="max",
        )
        is sentinel
    )
    assert calls == [
        (
            provider,
            {
                "api_key": "fixture-value",  # pragma: allowlist secret
                "model": model,
                "max_tokens": 4096,
                "effort": "max",
            },
        )
    ]
    with pytest.raises(llm_factory.UnknownProviderError, match="opnai"):
        llm_factory.build_operator_llm(
            "opnai", api_key=None, model="claude-opus-5", max_tokens=4096, effort="max"
        )
    assert len(calls) == 1


@pytest.mark.parametrize(
    ("model", "provider"),
    [
        ("claude-opus-5", "anthropic"),
        ("gpt-5.5", "openai"),
        ("chatgpt-latest", "openai"),
        ("o1", "openai"),
        ("o3", "openai"),
        ("o4-mini", "openai"),
        ("", None),
        ("ft:gpt-5.5:acme", None),
    ],
)
def test_model_family_prefixes(model: str, provider: str | None) -> None:
    """OPR-DEP-01: the decided prefixes classify only known model families."""
    assert llm_factory.model_provider(model) == provider
