"""Anthropic-backed operator LLM client.

Agent: operator
Role: adapt Anthropic tool-use responses to the kernel LLMClient protocol.
External I/O: Anthropic API when complete() is called.
"""

from __future__ import annotations

import importlib
import json

from kernel.llm_tokens import LLMUsage, llm_usage_or_none, usage_count


class ConfigurationError(RuntimeError):
    """Raised when the Anthropic client cannot be constructed safely."""


class AnthropicLLMClient:
    """Anthropic tool-use implementation of the operator LLM port."""

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
        self.last_usage: LLMUsage | None = None

    def complete(
        self, *, system: str, user: str, tool_schema: dict[str, object]
    ) -> str:
        """Call Anthropic with bounded intent or explanation tool output."""
        self.last_usage = None
        name = "parse_intent" if tool_schema else "answer_question"
        schema = tool_schema or {
            "type": "object",
            "properties": {"answer": {"type": "string"}},
            "required": ["answer"],
        }
        kwargs: dict[str, object] = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "output_config": {"effort": self.effort},
            "system": system,
            "messages": [{"role": "user", "content": user}],
            "tools": [
                {
                    "name": name,
                    "description": (
                        "Parse one operator command."
                        if tool_schema
                        else "Return one evidence-grounded answer."
                    ),
                    "input_schema": schema,
                }
            ],
            "tool_choice": {"type": "tool", "name": name},
        }
        response = self._client.messages.create(**kwargs)
        self.last_usage = _usage(response)
        data = _tool_input(response)
        return json.dumps(data) if tool_schema else str(data.get("answer", ""))


def _usage(response: object) -> LLMUsage | None:
    """Read Anthropic's usage block so operator calls price like every other.

    No `cache_control` marker here, unlike the deliberator. The operator sends
    a `tools` list that changes with `tool_schema` — `parse_intent` against
    `answer_question` — and tools render *ahead* of `system` in the cached
    prefix, so a marked system block would be invalidated by the very thing
    that varies per call. Marking it would write cache entries that are never
    read and bill 1.25x for the privilege.
    """
    return llm_usage_or_none(
        tokens_in=usage_count(response, "usage.input_tokens"),
        tokens_out=usage_count(response, "usage.output_tokens"),
        cache_read_tokens=usage_count(response, "usage.cache_read_input_tokens"),
        cache_write_tokens=usage_count(response, "usage.cache_creation_input_tokens"),
    )


def _tool_input(response: object) -> dict[str, object]:
    for block in getattr(response, "content", ()):
        if getattr(block, "type", None) == "tool_use":
            data = getattr(block, "input", {})
            return dict(data) if isinstance(data, dict) else {}
    return {"outcome": "refused", "reason": "model returned no tool result"}
