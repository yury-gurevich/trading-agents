"""LLM client protocol and deterministic fake implementation.

Agent: kernel
Role: define the minimal structured-completion port used by LLM-owning agents.
External I/O: none.
"""

from __future__ import annotations

from typing import Protocol


class LLMClient(Protocol):
    """Minimal structured completion interface."""

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
