"""Offline clients and candidates for Sprint 277's refusal proofs.

Agent: deliberator
Role: inject answers, status errors and a synchronized in-flight refusal.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.deliberator.model_chain import ModelChain, RoleCandidate
from agents.deliberator.turn_ledger import LedgerLLM

if TYPE_CHECKING:
    from threading import Barrier

    from kernel import InMemoryGraphStore

FIRST = "openai/gpt-5.5/high"
SECOND = "anthropic/claude-opus-5/max"
THIRD = "openai/gpt-third/low"
SWITCH = (
    f"deliberator-opponent switched to claude-opus-5 (passed over {FIRST}: http_429)"
)


class StatusError(Exception):
    """A vendor-shaped refusal whose untrusted text must not become the reason."""

    def __init__(self, status: object) -> None:
        self.status_code = status
        super().__init__("vendor detail deliberately excluded from switch metadata")


class Client:
    """Record the exact request and return or raise the injected result."""

    def __init__(self, result: str | Exception, barrier: Barrier | None = None) -> None:
        self.result = result
        self.barrier = barrier
        self.requests: list[tuple[str, str, dict[str, object]]] = []

    def complete(
        self, *, system: str, user: str, tool_schema: dict[str, object]
    ) -> str:
        self.requests.append((system, user, tool_schema))
        if self.barrier is not None:
            self.barrier.wait(timeout=10)
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


def chain(*clients: Client) -> ModelChain:
    """Give up to three stand-ins the literal declared labels."""
    return ModelChain(
        [
            RoleCandidate(label, label.split("/")[1], client)
            for label, client in zip((FIRST, SECOND, THIRD), clients, strict=False)
        ]
    )


def ledger(graph: InMemoryGraphStore, models: ModelChain, request: str) -> LedgerLLM:
    """Use a deliberately stale setting to expose a row naming the wrong model."""
    return LedgerLLM(
        graph,
        models,
        calling_agent="deliberator-opponent",
        model="stale-setting",
        correlation_id=request,
    )


def complete(call: LedgerLLM) -> str:
    """Send the same request shape to every candidate."""
    return call.complete(system="system", user="request", tool_schema={"name": "turn"})
