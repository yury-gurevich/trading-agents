"""OpenAI-backed deliberator LLM client.

Agent: deliberator
Role: adapt OpenAI free-text completions to the kernel LLMClient protocol, so a
      single provider outage cannot blind the veto.
External I/O: OpenAI API when complete() is called.

Exists because the Anthropic key hit its usage limit on 2026-08-08 and the veto
failed open on every order until 2026-09-01 ([DL-99](../../docs/design-log.md)).
A review that can only ever come from one vendor is not a review.
"""

from __future__ import annotations

import importlib


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

    def complete(
        self, *, system: str, user: str, tool_schema: dict[str, object]
    ) -> str:
        """Call OpenAI and return one free-text deliberation answer."""
        del tool_schema
        response = self._client.chat.completions.create(
            model=self.model,
            max_completion_tokens=self.max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return _text(response)


def _text(response: object) -> str:
    """Pull the assistant text out of a chat completion, tolerating empties."""
    parts: list[str] = []
    for choice in getattr(response, "choices", ()):
        message = getattr(choice, "message", None)
        content = getattr(message, "content", None)
        if content:
            parts.append(str(content))
    return "\n".join(parts)
