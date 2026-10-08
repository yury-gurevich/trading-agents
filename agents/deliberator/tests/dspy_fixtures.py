"""Immutable main records and canned clients for S254.

Agent: deliberator
Role: supply measured requests, responses and isolated served agents.
External I/O: reads the committed fixture; no model or network calls.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agents.deliberator.agent import DeliberatorAgent
from agents.deliberator.settings import DeliberatorSettings
from contracts.deliberator import DebateTurnRequest
from kernel import InMemoryGraphStore, InProcessBus
from kernel.llm import LLMCompletionStoppedError

MAIN = json.loads(
    (
        Path(__file__).resolve().parents[3]
        / "tests/fixtures/guided_turn_main_records.json"
    ).read_text("utf-8")
)


class Client:
    """Record the actual call; return text or raise the fixture's failure."""

    def __init__(self, answer: str | Exception) -> None:
        self.answer = answer
        self.calls: list[tuple[str, str]] = []

    def complete(
        self, *, system: str, user: str, tool_schema: dict[str, object]
    ) -> str:
        assert tool_schema == {}
        self.calls.append((system, user))
        if isinstance(self.answer, Exception):
            raise self.answer
        return self.answer


def answer_for(name: str) -> str | Exception:
    """Recreate precisely the text or exception used when main was captured."""
    row = next(a for a in MAIN["answers"] if a["name"] == name)
    if "completion" in row:
        return str(row["completion"])
    return {
        "stopped": LLMCompletionStoppedError(
            provider="anthropic", stop_reason="max_tokens"
        ),
        "transport": RuntimeError("provider down"),
        "timeout": TimeoutError("timed out"),
    }[name]


def request_for(case: dict[str, Any]) -> DebateTurnRequest:
    """Load the exact role and user case request from the immutable fixture."""
    row = next(
        r
        for r in MAIN["requests"]
        if (r["role"], r["user_case"]) == (case["role"], case["user_case"])
    )
    return DebateTurnRequest.model_validate(row["request"])


def served(role: str, client: Client) -> tuple[DeliberatorAgent, InMemoryGraphStore]:
    """Give each peer its own graph, bus and injected client."""
    graph = InMemoryGraphStore()
    agent = DeliberatorAgent(
        InProcessBus(),
        graph=graph,
        llm=client,
        settings=DeliberatorSettings(
            role="proponent" if role == "defender" else "opponent"
        ),
    )
    return agent, graph
