"""Anthropic-backed operator LLM client.

Agent: operator
Role: adapt Anthropic tool-use responses to the kernel LLMClient protocol.
External I/O: Anthropic API when complete() is called.
"""

from __future__ import annotations

import importlib
import json


class ConfigurationError(RuntimeError):
    """Raised when the Anthropic client cannot be constructed safely."""


class AnthropicLLMClient:
    """Anthropic tool-use implementation of the operator LLM port."""

    def __init__(
        self,
        *,
        api_key: str | None,
        model: str = "claude-sonnet-4-6",
        max_tokens: int = 512,
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

    def complete(
        self, *, system: str, user: str, tool_schema: dict[str, object]
    ) -> str:
        """Call Anthropic tool use and return the tool input as JSON."""
        response = self._client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
            tools=[
                {
                    "name": "parse_intent",
                    "description": "Parse one operator command.",
                    "input_schema": tool_schema,
                }
            ],
            tool_choice={"type": "tool", "name": "parse_intent"},
        )
        return json.dumps(_tool_input(response))


def _tool_input(response: object) -> dict[str, object]:
    for block in getattr(response, "content", ()):
        if getattr(block, "type", None) == "tool_use":
            data = getattr(block, "input", {})
            return dict(data) if isinstance(data, dict) else {}
    return {"outcome": "refused", "reason": "model returned no tool result"}
