"""Operator LLM call ledger context manager.

Agent: operator
Role: wrap the substrate LLM ledger with the operator's calling identity.
External I/O: GraphStore writes via the injected backend.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING

from agents.operator.prompt_recipe import PROMPT_RECIPE_HASH
from kernel import LLMCompletionStoppedError, llm_stop_reason, llm_usage
from kernel.llm_ledger import LLMCallCapture
from kernel.llm_ledger import record_llm_call as _record_llm_call

if TYPE_CHECKING:
    from collections.abc import Iterator

    from kernel import GraphStore, LLMClient


@contextmanager
def record_llm_call(
    graph: GraphStore,
    *,
    correlation_id: str,
    model: str,
    prompt: str,
    system_prompt: str = "",
) -> Iterator[LLMCallCapture]:
    """Persist one operator LLM call into the shared substrate ledger.

    The operator declares its own prompt recipe: its prompts are built by
    `agents/operator/domain/prompts.py`, not by the deliberation renderer, so
    sharing the deliberator's digest would assert something false about which
    code produced the row.
    """
    with _record_llm_call(
        graph,
        calling_agent="operator",
        correlation_id=correlation_id,
        model=model,
        prompt=prompt,
        system_prompt=system_prompt,
        prompt_recipe_hash=PROMPT_RECIPE_HASH,
    ) as capture:
        yield capture


def complete_recorded(
    call: LLMCallCapture,
    llm: LLMClient,
    *,
    system: str,
    user: str,
    tool_schema: dict[str, object],
) -> str | None:
    """Complete inside an open capture; None means the vendor cut the reply off.

    The stop reason and the usage are read on both paths: a reply cut at the cap
    was generated and billed in full, so a capture that read them only after a
    call that returned would record the dearest calls as costing nothing.
    """
    try:
        raw = llm.complete(system=system, user=user, tool_schema=tool_schema)
    except LLMCompletionStoppedError as exc:
        call.set_stop_reason(exc.stop_reason)
        call.set_usage(llm_usage(llm))
        return None
    call.set_response(raw)
    call.set_stop_reason(llm_stop_reason(llm))
    call.set_usage(llm_usage(llm))
    return raw
