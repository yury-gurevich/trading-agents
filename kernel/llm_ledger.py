"""Substrate LLM call ledger helpers.

Agent: kernel
Role: persist append-only LLMCall audit nodes for any model-calling agent.
External I/O: GraphStore writes via the injected backend.
"""

from __future__ import annotations

import hashlib
import time
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator

    from kernel.graph import GraphStore, Node


@dataclass
class LLMCallCapture:
    """Mutable call capture filled after the model returns."""

    prompt: str
    response: str = ""
    node: Node | None = None

    def set_response(self, response: str) -> None:
        """Record the raw model response for hashing and token estimates."""
        self.response = response


@contextmanager
def record_llm_call(
    graph: GraphStore,
    *,
    calling_agent: str,
    correlation_id: str,
    model: str,
    prompt: str,
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
            calling_agent=calling_agent,
            correlation_id=correlation_id,
            model=model,
            prompt_hash=_digest(capture.prompt),
            response_hash=_digest(capture.response),
            tokens_in=_rough_tokens(capture.prompt),
            tokens_out=_rough_tokens(capture.response),
            latency_ms=latency_ms,
        )


def write_llm_call(
    graph: GraphStore,
    *,
    calling_agent: str,
    correlation_id: str,
    model: str,
    prompt_hash: str,
    response_hash: str,
    tokens_in: int,
    tokens_out: int,
    latency_ms: int,
) -> Node:
    """Write one idempotent shared LLM call ledger node."""
    key = f"llmcall:{calling_agent}:{correlation_id}"
    current = graph.get_node("LLMCall", key)
    if current is not None:
        return current
    return graph.merge_node(
        "LLMCall",
        key,
        {
            "calling_agent": calling_agent,
            "correlation_id": correlation_id,
            "model": model,
            "prompt_hash": prompt_hash,
            "response_hash": response_hash,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "latency_ms": latency_ms,
            "created_at": datetime.now(tz=UTC).isoformat(),
        },
    )


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _rough_tokens(value: str) -> int:
    return max(1, len(value.split())) if value else 0
