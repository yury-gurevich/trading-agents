"""Choose a configured LLM provider without a fallback chain.

Agent: kernel
Role: construct the explicitly selected vendor client and provider defaults.
External I/O: none; constructed clients make the external calls.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from kernel.llm_anthropic import AnthropicLLMClient, OperatorAnthropicLLMClient
from kernel.llm_openai import OpenAILLMClient
from kernel.llm_openai_operator import OperatorOpenAILLMClient

if TYPE_CHECKING:
    from kernel.llm import LLMClient

Provider = Literal["anthropic", "openai"]

KEY_ENV: dict[str, str] = {
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
}

DEFAULT_MODEL: dict[str, str] = {
    "anthropic": "claude-opus-5",
    "openai": "gpt-5.5",
}

DEFAULT_OPERATOR_EFFORT: dict[str, str] = {"anthropic": "max", "openai": "xhigh"}

MODEL_PREFIXES: dict[str, tuple[str, ...]] = {
    "anthropic": ("claude-",),
    "openai": ("gpt-", "chatgpt-", "o1", "o3", "o4"),
}


class UnknownProviderError(RuntimeError):
    """Raised when configuration names a provider that does not exist."""


class ModelProviderMismatchError(RuntimeError):
    """Raised when an explicit model belongs to a different known provider."""


def build_llm(
    provider: str,
    *,
    api_key: str | None,
    model: str,
    max_tokens: int,
    effort: str | None,
) -> LLMClient:
    """Build exactly the selected provider; never silently switch vendors."""
    if provider == "anthropic":
        return AnthropicLLMClient(
            api_key=api_key, model=model, max_tokens=max_tokens, effort=effort or "max"
        )
    if provider == "openai":
        return OpenAILLMClient(
            api_key=api_key, model=model, max_tokens=max_tokens, effort=effort
        )
    raise UnknownProviderError(
        f"unknown llm_provider {provider!r}; expected one of {sorted(KEY_ENV)}"
    )


def default_model_for(provider: str) -> str:
    """Return the model this provider answers with when none is configured."""
    try:
        return DEFAULT_MODEL[provider]
    except KeyError as exc:
        raise UnknownProviderError(f"unknown llm_provider {provider!r}") from exc


def default_operator_effort_for(provider: str) -> str:
    """Return the selected provider's default operator reasoning effort."""
    try:
        return DEFAULT_OPERATOR_EFFORT[provider]
    except KeyError as exc:
        raise UnknownProviderError(f"unknown llm_provider {provider!r}") from exc


def model_provider(model: str) -> str | None:
    """Return the provider whose model family this name starts with, if any."""
    for provider, prefixes in MODEL_PREFIXES.items():
        if model.startswith(prefixes):
            return provider
    return None


def build_operator_llm(
    provider: str,
    *,
    api_key: str | None,
    model: str,
    max_tokens: int,
    effort: str,
) -> LLMClient:
    """Construct exactly the selected vendor's operator adapter."""
    owner = model_provider(model)
    if provider in KEY_ENV and owner not in (None, provider):
        raise ModelProviderMismatchError(
            f"model {model!r} belongs to {owner}; the declared llm_provider is "
            f"{provider}. Unset the model to use the provider's default."
        )
    if provider == "anthropic":
        return OperatorAnthropicLLMClient(
            api_key=api_key,
            model=model,
            max_tokens=max_tokens,
            effort=effort,
        )
    if provider == "openai":
        return OperatorOpenAILLMClient(
            api_key=api_key,
            model=model,
            max_tokens=max_tokens,
            effort=effort,
        )
    raise UnknownProviderError(f"unknown llm_provider {provider!r}")


def key_env_var(provider: str) -> str:
    """Return the env var holding this provider's key."""
    try:
        return KEY_ENV[provider]
    except KeyError as exc:
        raise UnknownProviderError(f"unknown llm_provider {provider!r}") from exc
