"""Anthropic-backed deliberator LLM client.

Agent: deliberator
Role: adapt Anthropic free-text completions to the kernel LLMClient protocol.
External I/O: Anthropic API when complete() is called.
"""

from __future__ import annotations

import importlib

from kernel.llm import STOP_REASON_UNKNOWN, LLMCompletionStoppedError
from kernel.llm_tokens import LLMUsage, llm_usage_or_none, usage_count


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
        self.last_usage: LLMUsage | None = None

    def complete(
        self, *, system: str, user: str, tool_schema: dict[str, object]
    ) -> str:
        """Call Anthropic and return one free-text deliberation answer."""
        del tool_schema
        self.last_usage = None
        response = self._client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            output_config={"effort": self.effort},
            system=cacheable_system(system),
            messages=[{"role": "user", "content": user}],
        )
        self.last_stop_reason = _stop_reason(response)
        self.last_usage = _usage(response)
        return _text(response)


def cacheable_system(system: str) -> list[dict[str, object]]:
    """Send the role's frozen system prompt as one cache-marked text block.

    The three deliberation system prompts are compiled artifacts (DL-42), byte
    identical on every request a run makes, and they render ahead of the
    per-order user prompt — so one cache entry per role per run serves every
    later request at roughly a tenth of the input rate. Before this the repo
    had never claimed it: `cache_read` was **0 across all 2,957 calls** of the
    S173 Part B round ([DL-160](../../docs/design-log.md)).

    🪤 It does not pay off for all three roles, and the marker cannot tell you
    so. Measured against `claude-opus-5` on 2026-09-13 via `count_tokens`:
    challenger **2,561** tokens and judge **2,474** clear the model's 512-token
    minimum cacheable prefix; the defender's **167** does not, so that role will
    report `cache_read_tokens=0` forever with no error and no cost. One code
    path is still right — a role-conditional marker would have to be re-derived
    every time a prompt or model changed, and the recorded counts already say
    which roles actually cached.
    """
    return [{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}]


def _usage(response: object) -> LLMUsage | None:
    """Read Anthropic's own usage block into the normalised kernel shape.

    `input_tokens` already **excludes** cached tokens on this API, so the three
    counts add up to billed input with no subtraction — the opposite of the
    OpenAI adapter, which must subtract. Measured against the live API
    2026-09-13: a cache-cold call returns
    `input_tokens=9, cache_read_input_tokens=0, cache_creation_input_tokens=0`.
    """
    return llm_usage_or_none(
        tokens_in=usage_count(response, "usage.input_tokens"),
        tokens_out=usage_count(response, "usage.output_tokens"),
        cache_read_tokens=usage_count(response, "usage.cache_read_input_tokens"),
        cache_write_tokens=usage_count(response, "usage.cache_creation_input_tokens"),
    )


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
