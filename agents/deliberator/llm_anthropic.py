"""Anthropic-backed deliberator LLM client.

Agent: deliberator
Role: adapt Anthropic free-text completions to the kernel LLMClient protocol.
External I/O: Anthropic API when complete() is called.
"""

from __future__ import annotations

import importlib

from kernel.llm import STOP_REASON_UNKNOWN, LLMCompletionStoppedError


class ConfigurationError(RuntimeError):
    """Raised when the Anthropic client cannot be constructed safely."""


class AnthropicLLMClient:
    """Anthropic implementation of the deliberation LLM port."""

    def __init__(
        self,
        *,
        api_key: str | None,
        model: str = "claude-opus-5",
        max_tokens: int = 4096,
        effort: str = "max",
    ) -> None:
        """Create the Anthropic client, failing early without credentials."""
        if not api_key:
            raise ConfigurationError("ANTHROPIC_API_KEY is required")
        try:
            anthropic = importlib.import_module("anthropic")
        except ModuleNotFoundError as exc:
            raise ConfigurationError("anthropic package is not installed") from exc
        self._client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens
        self.effort = effort
        self.last_stop_reason = STOP_REASON_UNKNOWN

    def complete(
        self, *, system: str, user: str, tool_schema: dict[str, object]
    ) -> str:
        """Call Anthropic and return one free-text deliberation answer."""
        del tool_schema
        response = self._client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            output_config={"effort": self.effort},
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        self.last_stop_reason = _stop_reason(response)
        return _text(response)


def _text(response: object) -> str:
    stop_reason = _stop_reason(response)
    if stop_reason == "max_tokens":
        raise LLMCompletionStoppedError(provider="anthropic", stop_reason=stop_reason)
    if stop_reason == "refusal":
        raise LLMCompletionStoppedError(
            provider="anthropic",
            stop_reason=stop_reason,
            category=_refusal_category(response),
        )
    parts: list[str] = []
    for block in getattr(response, "content", ()):
        if getattr(block, "type", None) == "text":
            parts.append(str(getattr(block, "text", "")))
    return "\n".join(part for part in parts if part)


def _stop_reason(response: object) -> str:
    reason = str(getattr(response, "stop_reason", "") or "").strip()
    return reason or STOP_REASON_UNKNOWN


def _refusal_category(response: object) -> str | None:
    details = getattr(response, "stop_details", None)
    if details is None:
        return None
    category = str(getattr(details, "category", "") or "").strip()
    return category or None
