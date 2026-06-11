"""Operator LLM call ledger context manager.

Agent: operator
Role: time and persist every LLM call made by the operator agent.
External I/O: GraphStore writes via the injected backend.
"""

from __future__ import annotations

import hashlib
import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import TYPE_CHECKING

from agents.operator.store import write_llm_call

if TYPE_CHECKING:
    from collections.abc import Iterator

    from kernel import GraphStore, Node


@dataclass
class LLMCallCapture:
    """Mutable call capture filled by the operator after the model returns."""

    prompt: str
    response: str = ""
    node: Node | None = None

    def set_response(self, response: str) -> None:
        """Record the raw model response for hashing and token estimates."""
        self.response = response


@contextmanager
def record_llm_call(
    graph: GraphStore, *, correlation_id: str, model: str, prompt: str
) -> Iterator[LLMCallCapture]:
    """Persist one LLM call after the wrapped completion finishes."""
    started = time.perf_counter()
    capture = LLMCallCapture(prompt=prompt)
    try:
        yield capture
    finally:
        latency_ms = int((time.perf_counter() - started) * 1000)
        capture.node = write_llm_call(
            graph,
            correlation_id=correlation_id,
            model=model,
            prompt_hash=_digest(capture.prompt),
            response_hash=_digest(capture.response),
            tokens_in=_rough_tokens(capture.prompt),
            tokens_out=_rough_tokens(capture.response),
            latency_ms=latency_ms,
        )


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _rough_tokens(value: str) -> int:
    return max(1, len(value.split())) if value else 0
