"""Anthropic LLM adapters over one shared transport.

Agent: kernel
Role: adapt Anthropic free-text and tool-use responses to the LLM port.
External I/O: Anthropic API when a client completes a request.
"""

from __future__ import annotations

import importlib
import json
from typing import TYPE_CHECKING

from kernel.llm import STOP_REASON_UNKNOWN
from kernel.llm_anthropic_responses import (
    _stop_reason,
    _text,
    _tool_input,
    _usage,
    cacheable_system,
)

if TYPE_CHECKING:
    from kernel.llm_tokens import LLMUsage


class ConfigurationError(RuntimeError):
    """Raised when the Anthropic client cannot be constructed safely."""


class _AnthropicTransport:
    """Own Anthropic configuration, SDK construction, and request transport."""

    def __init__(self, *, api_key: str | None) -> None:
        if not api_key:
            raise ConfigurationError("ANTHROPIC_API_KEY is required")
        try:
            anthropic = importlib.import_module("anthropic")
        except ModuleNotFoundError as exc:
            raise ConfigurationError("anthropic package is not installed") from exc
        self._client = anthropic.Anthropic(api_key=api_key)

    def create(self, **kwargs: object) -> object:
        """Send one request without exposing configuration beyond this boundary."""
        return self._client.messages.create(**kwargs)


class _AnthropicClient:
    """Store the common client configuration and vendor-usage handling."""

    def __init__(
        self,
        *,
        api_key: str | None,
        model: str,
        max_tokens: int,
        effort: str,
    ) -> None:
        self._transport = _AnthropicTransport(api_key=api_key)
        self._client = self._transport._client
        self.model = model
        self.max_tokens = max_tokens
        self.effort = effort
        self.last_usage: LLMUsage | None = None

    def _request(self, **kwargs: object) -> object:
        self.last_usage = None
        response = self._transport.create(**kwargs)
        self.last_usage = _usage(response)
        return response


class AnthropicLLMClient(_AnthropicClient):
    """Anthropic free-text implementation used by deliberation."""

    def __init__(
        self,
        *,
        api_key: str | None,
        model: str = "claude-opus-5",
        max_tokens: int = 4096,
        effort: str = "max",
    ) -> None:
        """Build the shared free-text client with deliberation defaults."""
        super().__init__(
            api_key=api_key,
            model=model,
            max_tokens=max_tokens,
            effort=effort,
        )
        self.last_stop_reason = STOP_REASON_UNKNOWN

    def complete(
        self, *, system: str, user: str, tool_schema: dict[str, object]
    ) -> str:
        """Call Anthropic and return one free-text deliberation answer."""
        del tool_schema
        response = self._request(
            model=self.model,
            max_tokens=self.max_tokens,
            output_config={"effort": self.effort},
            system=cacheable_system(system),
            messages=[{"role": "user", "content": user}],
        )
        self.last_stop_reason = _stop_reason(response)
        return _text(response)


class OperatorAnthropicLLMClient(_AnthropicClient):
    """Anthropic tool-use implementation used by operator commands and explanations."""

    def __init__(
        self,
        *,
        api_key: str | None,
        model: str = "claude-opus-5",
        max_tokens: int = 4096,
        effort: str = "max",
    ) -> None:
        """Build the shared tool-use client with operator defaults."""
        super().__init__(
            api_key=api_key,
            model=model,
            max_tokens=max_tokens,
            effort=effort,
        )

    def complete(
        self, *, system: str, user: str, tool_schema: dict[str, object]
    ) -> str:
        """Call Anthropic with a bounded tool-use response."""
        name = "parse_intent" if tool_schema else "answer_question"
        schema = tool_schema or {
            "type": "object",
            "properties": {"answer": {"type": "string"}},
            "required": ["answer"],
        }
        response = self._request(
            model=self.model,
            max_tokens=self.max_tokens,
            output_config={"effort": self.effort},
            system=system,
            messages=[{"role": "user", "content": user}],
            tools=[
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
            tool_choice={"type": "tool", "name": name},
        )
        data = _tool_input(response)
        return json.dumps(data) if tool_schema else str(data.get("answer", ""))
