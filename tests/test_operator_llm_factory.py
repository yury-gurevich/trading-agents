"""Selected-provider operator factory tests.

Agent: kernel
Role: prove exactly one provider is constructed and no failure changes vendors.
External I/O: none; constructors are fake.
"""

import pytest

from kernel import llm_factory

TEST_CREDENTIAL = "fixture-value"


@pytest.mark.parametrize("provider", ["anthropic", "openai"])
def test_b4_factory_builds_exactly_selected_vendor(
    monkeypatch: pytest.MonkeyPatch, provider: str
) -> None:
    """OPR-DEP-01: both configured providers use their own operator client."""
    calls: list[str] = []
    sentinel = object()

    def anthropic(**kwargs: object) -> object:
        calls.append("anthropic")
        return sentinel

    def openai(**kwargs: object) -> object:
        calls.append("openai")
        return sentinel

    monkeypatch.setattr(llm_factory, "OperatorAnthropicLLMClient", anthropic)
    monkeypatch.setattr(llm_factory, "OperatorOpenAILLMClient", openai)
    assert (
        llm_factory.build_operator_llm(
            provider,
            api_key=TEST_CREDENTIAL,
            model="explicit",
            max_tokens=4096,
            effort="max",
        )
        is sentinel
    )
    assert calls == [provider]


@pytest.mark.parametrize("provider", ["anthropic", "openai"])
def test_b4_selected_failure_never_builds_other_vendor(
    monkeypatch: pytest.MonkeyPatch, provider: str
) -> None:
    """OPR-DEP-01: failure of the chosen constructor propagates with no fallback."""
    calls: list[str] = []

    def broken(**kwargs: object) -> object:
        calls.append(provider)
        raise RuntimeError("selected unavailable")

    def other(**kwargs: object) -> object:
        calls.append("other")
        return object()

    classes = {
        "anthropic": "OperatorAnthropicLLMClient",
        "openai": "OperatorOpenAILLMClient",
    }
    for vendor, name in classes.items():
        monkeypatch.setattr(llm_factory, name, broken if vendor == provider else other)
    with pytest.raises(RuntimeError, match="selected unavailable"):
        llm_factory.build_operator_llm(
            provider,
            api_key=TEST_CREDENTIAL,
            model="explicit",
            max_tokens=4096,
            effort="max",
        )
    assert calls == [provider]


def test_b4_unknown_provider_refuses() -> None:
    """OPR-DEP-01: an unknown vendor never becomes an implicit default."""
    with pytest.raises(llm_factory.UnknownProviderError, match="opnai"):
        llm_factory.build_operator_llm(
            "opnai", api_key=None, model="explicit", max_tokens=4096, effort="max"
        )
