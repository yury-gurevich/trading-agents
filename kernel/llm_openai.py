"""OpenAI free-text LLM adapter.

Agent: kernel
Role: adapt OpenAI free-text completions to the LLM port.
External I/O: OpenAI API when complete() is called.
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
        effort: str | None = "max",
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
        kwargs: dict[str, object] = {
            "model": self.model,
            "max_completion_tokens": self.max_tokens,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        if self.effort is not None:
            kwargs["reasoning_effort"] = self.effort
        response = self._client.chat.completions.create(**kwargs)
        self.last_stop_reason = _stop_reason(response)
        self.last_usage = _usage(response)
        return _text(response)


def _usage(response: object) -> LLMUsage | None:
    """Read OpenAI usage, separating cached input from billable input."""
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
