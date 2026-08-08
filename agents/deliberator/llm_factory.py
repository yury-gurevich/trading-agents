"""Choose the deliberator's LLM provider from configuration.

Agent: deliberator
Role: build the configured provider's client, and name the choice as a fact rather
      than leaving it implicit in an entrypoint.
External I/O: none (constructs a client; the client does the I/O).

The provider is a **tunable**, not a fallback chain: an automatic silent switch
would make "which model reviewed this order" unanswerable after the fact, and the
whole point of the veto is that its reasoning is attributable. Switching is an
operator act, one env var, recorded in the DeliberationRun's role models.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from kernel.llm import LLMClient

Provider = Literal["anthropic", "openai"]

#: Env var holding the key for each provider.
KEY_ENV: dict[str, str] = {
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
}


class UnknownProviderError(RuntimeError):
    """Raised when configuration names a provider that does not exist."""


def build_llm(
    provider: str,
    *,
    api_key: str | None,
    model: str,
    max_tokens: int,
    effort: str,
) -> LLMClient:
    """Return the client for `provider`, raising on an unknown name.

    An unknown provider must raise rather than defaulting: silently falling back to
    the other vendor is how a misconfiguration becomes an unnoticed change of who
    reviewed the trade.
    """
    if provider == "anthropic":
        from agents.deliberator.llm_anthropic import AnthropicLLMClient

        return AnthropicLLMClient(
            api_key=api_key, model=model, max_tokens=max_tokens, effort=effort
        )
    if provider == "openai":
        from agents.deliberator.llm_openai import OpenAILLMClient

        return OpenAILLMClient(
            api_key=api_key, model=model, max_tokens=max_tokens, effort=effort
        )
    raise UnknownProviderError(
        f"unknown llm_provider {provider!r}; expected one of {sorted(KEY_ENV)}"
    )


def key_env_var(provider: str) -> str:
    """Return the env var holding this provider's key."""
    try:
        return KEY_ENV[provider]
    except KeyError as exc:
        raise UnknownProviderError(f"unknown llm_provider {provider!r}") from exc
