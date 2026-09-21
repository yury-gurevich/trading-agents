"""Choose a configured LLM provider without a fallback chain.

Agent: kernel
Role: construct the explicitly selected vendor client and provider defaults.
External I/O: none; constructed clients make the external calls.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from kernel.llm_anthropic import AnthropicLLMClient
from kernel.llm_openai import OpenAILLMClient

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


class UnknownProviderError(RuntimeError):
    """Raised when configuration names a provider that does not exist."""


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


def key_env_var(provider: str) -> str:
    """Return the env var holding this provider's key."""
    try:
        return KEY_ENV[provider]
    except KeyError as exc:
        raise UnknownProviderError(f"unknown llm_provider {provider!r}") from exc
