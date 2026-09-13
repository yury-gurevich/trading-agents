"""OpenAI-backed deliberator LLM client.

Agent: deliberator
Role: adapt OpenAI free-text completions to the kernel LLMClient protocol, so a
      single provider outage cannot blind the veto.
External I/O: OpenAI API when complete() is called.

Exists because the Anthropic key hit its usage limit on 2026-08-08 and the veto
failed open on every order until 2026-09-01 ([DL-99](../../docs/design-log.md)).
A review that can only ever come from one vendor is not a review.

`effort` reaches OpenAI as `reasoning_effort`. Pass-through is total, not
best-effort: our `Effort` literal is a strict *subset* of the SDK's
`ReasoningEffort` (measured against `openai` 2.49.0, which also accepts `none`
and `minimal`), so every value the tunable can hold is already valid on the
wire. `test_our_effort_values_are_all_valid_openai_values` pins that; widening
`Effort` without checking it would 400 at run time
([DL-105](../../docs/design-log.md)).
"""

from __future__ import annotations

import importlib

from kernel.llm import STOP_REASON_UNKNOWN, LLMCompletionStoppedError
from kernel.llm_tokens import LLMUsage, llm_usage_or_none, usage_count


class ConfigurationError(RuntimeError):
    """Raised when the OpenAI client cannot be constructed safely."""


class OpenAILLMClient:
    """OpenAI implementation of the deliberation LLM port."""

    def __init__(
        self,
        *,
        api_key: str | None,
        model: str = "gpt-5.5",
        max_tokens: int = 4096,
        effort: str = "max",
    ) -> None:
        """Create the OpenAI client, failing early without credentials."""
        if not api_key:
            raise ConfigurationError("OPENAI_API_KEY is required")
        try:
            openai = importlib.import_module("openai")
        except ModuleNotFoundError as exc:
            raise ConfigurationError("openai package is not installed") from exc
        self._client = openai.OpenAI(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens
        self.effort = effort
        self.last_stop_reason = STOP_REASON_UNKNOWN
        self.last_usage: LLMUsage | None = None

    def complete(
        self, *, system: str, user: str, tool_schema: dict[str, object]
    ) -> str:
        """Call OpenAI and return one free-text deliberation answer."""
        del tool_schema
        self.last_usage = None
        response = self._client.chat.completions.create(
            model=self.model,
            max_completion_tokens=self.max_tokens,
            reasoning_effort=self.effort,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        self.last_stop_reason = _stop_reason(response)
        self.last_usage = _usage(response)
        return _text(response)


def _usage(response: object) -> LLMUsage | None:
    """Read OpenAI's usage block into the normalised kernel shape.

    🪤 `prompt_tokens` **includes** `prompt_tokens_details.cached_tokens` here,
    the opposite of Anthropic, where `input_tokens` excludes them. The kernel's
    `tokens_in` is defined as the *uncached* input, so the cached part is
    subtracted — mapping the field straight across would count every cached
    token twice and overstate the bill it was just fixed to report honestly.
    Clamped at zero: a vendor that ever reported more cached than prompt tokens
    must not produce a negative count.

    There is no cache-*write* count because OpenAI's prompt caching is
    automatic and unbilled — `cache_write_tokens` stays 0 by construction, not
    because the field was forgotten.
    """
    prompt_tokens = usage_count(response, "usage.prompt_tokens")
    cached = usage_count(response, "usage.prompt_tokens_details.cached_tokens")
    return llm_usage_or_none(
        tokens_in=max(0, prompt_tokens - cached),
        tokens_out=usage_count(response, "usage.completion_tokens"),
        cache_read_tokens=min(cached, prompt_tokens),
    )


def _text(response: object) -> str:
    """Pull the assistant text out of a chat completion."""
    if "length" in _finish_reasons(response):
        raise LLMCompletionStoppedError(provider="openai", stop_reason="length")
    parts: list[str] = []
    for choice in getattr(response, "choices", ()):
        message = getattr(choice, "message", None)
        content = getattr(message, "content", None)
        if content:
            parts.append(str(content))
    return "\n".join(parts)


def _stop_reason(response: object) -> str:
    reasons = _finish_reasons(response)
    return "+".join(dict.fromkeys(reasons)) if reasons else STOP_REASON_UNKNOWN


def _finish_reasons(response: object) -> tuple[str, ...]:
    reasons: list[str] = []
    for choice in getattr(response, "choices", ()):
        reason = str(getattr(choice, "finish_reason", "") or "").strip()
        if reason:
            reasons.append(reason)
    return tuple(reasons)
