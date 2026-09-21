"""Anthropic response-shape parsing helpers.

Agent: kernel
Role: normalise Anthropic usage, tool-use, and free-text response shapes.
External I/O: none.
"""

from __future__ import annotations

from kernel.llm import STOP_REASON_UNKNOWN, LLMCompletionStoppedError
from kernel.llm_tokens import LLMUsage, llm_usage_or_none, usage_count


def cacheable_system(system: str) -> list[dict[str, object]]:
    """Mark deliberation's stable role prompt as an ephemeral cache block."""
    return [{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}]


def _usage(response: object) -> LLMUsage | None:
    """Read Anthropic's usage block into the normalised kernel shape."""
    return llm_usage_or_none(
        tokens_in=usage_count(response, "usage.input_tokens"),
        tokens_out=usage_count(response, "usage.output_tokens"),
        cache_read_tokens=usage_count(response, "usage.cache_read_input_tokens"),
        cache_write_tokens=usage_count(response, "usage.cache_creation_input_tokens"),
    )


def _tool_input(response: object) -> dict[str, object]:
    """Extract the structured tool payload or its existing refusal fallback."""
    for block in getattr(response, "content", ()):
        if getattr(block, "type", None) == "tool_use":
            data = getattr(block, "input", {})
            return dict(data) if isinstance(data, dict) else {}
    return {"outcome": "refused", "reason": "model returned no tool result"}


def _text(response: object) -> str:
    """Read a clean free-text completion or raise for a stopped one."""
    stop_reason = _stop_reason(response)
    if stop_reason == "max_tokens":
        raise LLMCompletionStoppedError(provider="anthropic", stop_reason=stop_reason)
    if stop_reason == "refusal":
        raise LLMCompletionStoppedError(
            provider="anthropic",
            stop_reason=stop_reason,
            category=_refusal_category(response),
        )
    parts = [
        str(getattr(block, "text", ""))
        for block in getattr(response, "content", ())
        if getattr(block, "type", None) == "text"
    ]
    return "\n".join(part for part in parts if part)


def _stop_reason(response: object) -> str:
    reason = str(getattr(response, "stop_reason", "") or "").strip()
    return reason or STOP_REASON_UNKNOWN


def _refusal_category(response: object) -> str | None:
    details = getattr(response, "stop_details", None)
    category = str(getattr(details, "category", "") or "").strip()
    return category or None
