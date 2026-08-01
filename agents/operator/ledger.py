"""Operator LLM call ledger context manager.

Agent: operator
Role: wrap the substrate LLM ledger with the operator's calling identity.
External I/O: GraphStore writes via the injected backend.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING

from kernel.llm_ledger import LLMCallCapture
from kernel.llm_ledger import record_llm_call as _record_llm_call

if TYPE_CHECKING:
    from collections.abc import Iterator

    from kernel import GraphStore


@contextmanager
def record_llm_call(
    graph: GraphStore, *, correlation_id: str, model: str, prompt: str
) -> Iterator[LLMCallCapture]:
    """Persist one operator LLM call into the shared substrate ledger."""
    with _record_llm_call(
        graph,
        calling_agent="operator",
        correlation_id=correlation_id,
        model=model,
        prompt=prompt,
    ) as capture:
        yield capture
