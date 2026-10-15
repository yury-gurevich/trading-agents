"""A7-A9 and A12: startup uses exactly the handed-over candidates.

Agent: deliberator
Role: prove fallback parsing, injected construction and entrypoint wiring.
External I/O: none; real OpenAI clients are constructed but never called.
"""

import inspect

import pytest

from agents.deliberator.entrypoint import build_role_models, main
from agents.deliberator.model_chain import ModelChain, build_role_chain
from agents.deliberator.settings import DeliberatorSettings
from agents.deliberator.tests.refusal_testkit import FIRST, SECOND, Client
from kernel import LLMClient
from kernel.llm_factory import ModelProviderMismatchError, UnknownProviderError
from kernel.llm_openai import OpenAILLMClient


def test_a7_handed_candidates_build_with_their_own_vendor_key() -> None:
    """DLIB-DEP-05: chosen client first; each fallback gets its own complete config."""
    settings = DeliberatorSettings(
        _env_file=None,
        role="opponent",
        llm_provider="openai",
        challenger_model="gpt-5.5",
        effort="high",
        llm_fallbacks=f" {SECOND} ,,",
    )
    first, second = Client("first"), Client("second")
    value = "fixture-value"
    calls: list[tuple[str, dict[str, object]]] = []

    def build(vendor: str, **kwargs: object) -> LLMClient:
        calls.append((vendor, kwargs))
        return second

    models = build_role_chain(
        settings, {"ANTHROPIC_API_KEY": value}, first, build=build
    )
    assert [candidate.label for candidate in models.candidates] == [FIRST, SECOND]
    assert models.current().client is first
    assert models.candidates[1].client is second
    assert calls == [
        (
            "anthropic",
            {
                "api_key": value,
                "model": "claude-opus-5",
                "max_tokens": settings.max_tokens,
                "effort": "max",
            },
        )
    ]
    empty = settings.model_copy(update={"llm_fallbacks": ""})
    alone = build_role_chain(empty, {}, first, build=build)
    assert [candidate.label for candidate in alone.candidates] == [FIRST]
    assert len(calls) == 1


@pytest.mark.parametrize(
    "label",
    [
        "anthropic/claude-opus-5",
        "anthropic//max",
        "a/b/c/d",
        "/claude-opus-5/max",
    ],
)
def test_a8_unreadable_fallback_stops_before_build(label: str) -> None:
    """DLIB-DEP-05: a malformed handed-over label never creates a partial chain."""
    settings = DeliberatorSettings(_env_file=None, llm_fallbacks=label)
    calls: list[str] = []

    def build(vendor: str, **kwargs: object) -> LLMClient:
        calls.append(vendor)
        return Client("unused")

    with pytest.raises(ValueError, match="unreadable LLM fallback"):
        build_role_chain(settings, {}, Client("first"), build=build)
    assert calls == []


@pytest.mark.parametrize(
    ("label", "error"),
    [
        ("anthropic/gpt-5.5/max", ModelProviderMismatchError),
        ("opnai/gpt-5.5/high", UnknownProviderError),
    ],
)
def test_a9_kernel_refuses_unrunnable_fallback(
    label: str, error: type[Exception]
) -> None:
    """DLIB-NEV-11 / DLIB-DEP-05: the kernel guards every fallback before a call."""
    settings = DeliberatorSettings(_env_file=None, llm_fallbacks=label)
    with pytest.raises(error):
        build_role_chain(settings, {}, Client("first"))


def test_a9_empty_chain_is_refused() -> None:
    """DLIB-DEP-05: a role cannot run without a candidate."""
    with pytest.raises(ValueError, match="at least one LLM candidate"):
        ModelChain(())


def test_a12_entrypoint_builds_and_uses_role_chain() -> None:
    """DLIB-DEP-05: main builds both handed-over efforts after activation."""
    settings = DeliberatorSettings(
        _env_file=None,
        role="proponent",
        llm_provider="openai",
        defender_model="gpt-5.5",
        effort="high",
        llm_fallbacks="openai/gpt-5.5/xhigh",
    )
    models = build_role_models(settings, {"OPENAI_API_KEY": "fixture-value"})
    assert [candidate.label for candidate in models.candidates] == [
        FIRST,
        "openai/gpt-5.5/xhigh",
    ]
    efforts = []
    for candidate in models.candidates:
        assert isinstance(candidate.client, OpenAILLMClient)
        efforts.append(candidate.client.effort)
    assert efforts == ["high", "xhigh"]
    source = inspect.getsource(main)
    assert "build_role_models(settings, os.environ)" in source
    assert source.index("activated_settings(") < source.index("build_role_models(")
