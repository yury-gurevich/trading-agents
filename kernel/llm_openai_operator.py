"""OpenAI forced-function adapter for operator commands and explanations.

Agent: kernel
Role: return one forced function's arguments or evidence-grounded answer.
External I/O: OpenAI Responses API over HTTPS.
"""

from __future__ import annotations

import importlib
import json

from kernel.llm import STOP_REASON_UNKNOWN, LLMCompletionStoppedError
from kernel.llm_openai import ConfigurationError
from kernel.llm_tokens import LLMUsage, llm_usage_or_none, usage_count

_ANSWER_SCHEMA: dict[str, object] = {
    "type": "object",
    "properties": {"answer": {"type": "string"}},
    "required": ["answer"],
}
_REFUSAL = {"outcome": "refused", "reason": "model returned no tool result"}
_CUT_OFF = "max_output_tokens"


class OperatorOpenAILLMClient:
    """OpenAI function-calling implementation of the operator LLM port."""

    def __init__(
        self,
        *,
        api_key: str | None,
        model: str = "gpt-5.5",
        max_tokens: int = 4096,
        effort: str = "xhigh",
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
        """Force one named function, recording usage even for a cut-off reply."""
        name = "parse_intent" if tool_schema else "answer_question"
        self.last_usage = None
        self.last_stop_reason = STOP_REASON_UNKNOWN
        response = self._client.responses.create(
            model=self.model,
            max_output_tokens=self.max_tokens,
            reasoning={"effort": self.effort},
            instructions=system,
            input=user,
            tools=[
                {
                    "type": "function",
                    "name": name,
                    "description": "Parse one operator command."
                    if tool_schema
                    else "Return one evidence-grounded answer.",
                    "parameters": tool_schema or _ANSWER_SCHEMA,
                    "strict": False,
                }
            ],
            tool_choice={"type": "function", "name": name},
            store=False,
        )
        self.last_stop_reason = response_stop_reason(response)
        self.last_usage = response_usage(response)
        if self.last_stop_reason == _CUT_OFF:
            raise LLMCompletionStoppedError(provider="openai", stop_reason=_CUT_OFF)
        data = _arguments(response)
        return json.dumps(data) if tool_schema else str(data.get("answer", ""))


def response_stop_reason(response: object) -> str:
    """Keep the vendor's incomplete reason, otherwise its status or unknown."""
    details = getattr(response, "incomplete_details", None)
    reason = str(getattr(details, "reason", "") or "").strip()
    status = str(getattr(response, "status", "") or "").strip()
    return reason or status or STOP_REASON_UNKNOWN


def response_usage(response: object) -> LLMUsage | None:
    """Separate cached input from uncached input without reading cache writes."""
    input_tokens = usage_count(response, "usage.input_tokens")
    cached = usage_count(response, "usage.input_tokens_details.cached_tokens")
    return llm_usage_or_none(
        tokens_in=max(0, input_tokens - cached),
        tokens_out=usage_count(response, "usage.output_tokens"),
        cache_read_tokens=min(cached, input_tokens),
    )


def _arguments(response: object) -> dict[str, object]:
    for item in getattr(response, "output", None) or ():
        if getattr(item, "type", "") != "function_call":
            continue
        try:
            data = json.loads(getattr(item, "arguments", ""))
        except (TypeError, ValueError):
            return dict(_REFUSAL)
        return dict(data) if isinstance(data, dict) else dict(_REFUSAL)
    return dict(_REFUSAL)
