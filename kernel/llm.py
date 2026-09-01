"""LLM client protocol and deterministic fake implementation.

Agent: kernel
Role: define the minimal structured-completion port used by LLM-owning agents.
External I/O: none.
"""

from __future__ import annotations

from typing import Protocol

STOP_REASON_UNKNOWN = "unknown"


class LLMCompletionStoppedError(RuntimeError):
    """Raised when a provider reports that a completion did not finish cleanly."""

    def __init__(
        self,
        *,
        provider: str,
        stop_reason: str,
        category: str | None = None,
    ) -> None:
        """Build a payload-free error from provider stop metadata."""
        self.provider = provider
        self.stop_reason = _clean_stop_reason(stop_reason)
        self.category = _clean_optional_stop_reason(category)
        message = f"{provider} completion stopped: stop_reason={self.stop_reason}"
        if self.category:
            message = f"{message} category={self.category}"
        super().__init__(message)


def llm_stop_reason(client: object) -> str:
    """Return the last sanitized stop reason exposed by an LLM client."""
    return _clean_stop_reason(getattr(client, "last_stop_reason", None))


def _clean_stop_reason(value: object) -> str:
    text = str(value or "").strip()
    return text if text else STOP_REASON_UNKNOWN


def _clean_optional_stop_reason(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


class LLMClient(Protocol):
    """Minimal structured completion interface.

    Implementations that can see provider stop metadata expose it as
    ``last_stop_reason`` after each call, and raise
    ``LLMCompletionStoppedError`` for vendor-declared truncation or refusal.
    """

    def complete(
        self, *, system: str, user: str, tool_schema: dict[str, object]
    ) -> str:
        """Return the model's structured tool result as a JSON string."""
        ...  # pragma: no cover - protocol declaration only.


class FakeLLMClient:
    """Deterministic keyword-matching LLM stub for CI and local tests."""

    def __init__(self, responses: dict[str, str]) -> None:
        """Store canned responses keyed by case-insensitive user-text substrings."""
        self._responses = responses

    def complete(
        self, *, system: str, user: str, tool_schema: dict[str, object]
    ) -> str:
        """Return the first canned response whose key appears in the user text."""
        del system, tool_schema
        for key, response in self._responses.items():
            if key.lower() in user.lower():
                return response
        return '{"family": "status", "parameters": {}, "outcome": "intent"}'
