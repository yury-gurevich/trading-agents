"""OpenAI forced-function adapter for operator commands and explanations.

Agent: kernel
Role: return one forced function's arguments or evidence-grounded answer.
External I/O: OpenAI Chat Completions API over HTTPS.
"""

from __future__ import annotations

import importlib
import json
from typing import TYPE_CHECKING

from kernel.llm import STOP_REASON_UNKNOWN, LLMCompletionStoppedError
from kernel.llm_openai import (
    ConfigurationError,
    completion_stop_reason,
    completion_usage,
)

if TYPE_CHECKING:
    from kernel.llm_tokens import LLMUsage

_ANSWER_SCHEMA: dict[str, object] = {
    "type": "object",
    "properties": {"answer": {"type": "string"}},
    "required": ["answer"],
}
_REFUSAL = {"outcome": "refused", "reason": "model returned no tool result"}


class OperatorOpenAILLMClient:
    """OpenAI function-calling implementation of the operator LLM port."""

    def __init__(
        self,
        *,
        api_key: str | None,
        model: str = "gpt-5.5",
        max_tokens: int = 4096,
        effort: str = "max",
    ) -> None:
        """Fail early without credentials or the optional vendor SDK."""
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
        """Force one named function, recording usage even for a length stop."""
        name = "parse_intent" if tool_schema else "answer_question"
        self.last_usage = None
        self.last_stop_reason = STOP_REASON_UNKNOWN
        response = self._client.chat.completions.create(
            model=self.model,
            max_completion_tokens=self.max_tokens,
            reasoning_effort=self.effort,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            tools=[
                {
                    "type": "function",
                    "function": {
                        "name": name,
                        "description": "Parse one operator command."
                        if tool_schema
                        else "Return one evidence-grounded answer.",
                        "parameters": tool_schema or _ANSWER_SCHEMA,
                    },
                }
            ],
            tool_choice={"type": "function", "function": {"name": name}},
        )
        self.last_stop_reason = completion_stop_reason(response)
        self.last_usage = completion_usage(response)
        if "length" in self.last_stop_reason.split("+"):
            raise LLMCompletionStoppedError(provider="openai", stop_reason="length")
        data = _arguments(response)
        return json.dumps(data) if tool_schema else str(data.get("answer", ""))


def _arguments(response: object) -> dict[str, object]:
    for choice in getattr(response, "choices", ()):
        message = getattr(choice, "message", None)
        for call in getattr(message, "tool_calls", None) or ():
            raw = getattr(getattr(call, "function", None), "arguments", "")
            try:
                data = json.loads(raw)
            except (TypeError, ValueError):
                return dict(_REFUSAL)
            return dict(data) if isinstance(data, dict) else dict(_REFUSAL)
    return dict(_REFUSAL)
