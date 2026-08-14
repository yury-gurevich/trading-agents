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

#: Model each provider answers with when the operator names no model.
#:
#: A provider switch that still carries the other vendor's model name is not a
#: switch: it sends `claude-opus-5` to OpenAI, and — worse — stamps that name on
#: the DeliberationRun as the model that reviewed the order (DL-100). The default
#: therefore belongs to the provider, next to its key, not to the role tunable.
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
