"""Operator graph write path.

Agent: operator
Role: write LLM call ledger, command audits, and typed intents.
External I/O: GraphStore writes via the injected backend.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from contracts.operator import TypedIntent
    from kernel import GraphStore, Node


def write_llm_call(
    graph: GraphStore,
    *,
    correlation_id: str,
    model: str,
    prompt_hash: str,
    response_hash: str,
    tokens_in: int,
    tokens_out: int,
    latency_ms: int,
) -> Node:
    """Write one idempotent LLM call ledger node."""
    key = f"llmcall:{correlation_id}"
    current = graph.get_node("LLMCall", key)
    if current is not None:
        return current
    return graph.merge_node(
        "LLMCall",
        key,
        {
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


def write_command_audit(
    graph: GraphStore,
    *,
    correlation_id: str,
    actor: str,
    channel: str,
    text: str,
    outcome: str,
    llm_call_node: Node,
) -> Node:
    """Write one idempotent command audit and link it to the LLM call."""
    key = f"audit:{correlation_id}"
    node = graph.get_node("CommandAudit", key)
    if node is None:
        node = graph.merge_node(
            "CommandAudit",
            key,
            {
                "correlation_id": correlation_id,
                "actor": actor,
                "channel": channel,
                "text": text,
                "outcome": outcome,
                "created_at": datetime.now(tz=UTC).isoformat(),
            },
        )
    graph.add_edge(node, llm_call_node, "PRODUCED_BY")
    return node


def write_intent(
    graph: GraphStore, *, correlation_id: str, audit_node: Node, intent: TypedIntent
) -> Node:
    """Write one idempotent intent and link it to the command audit."""
    key = f"intent:{correlation_id}"
    node = graph.get_node("Intent", key)
    if node is None:
        node = graph.merge_node(
            "Intent",
            key,
            {
                "family": intent.family,
                "parameters": json.dumps(intent.parameters, sort_keys=True),
                "requires_confirmation": intent.requires_confirmation,
            },
        )
    graph.add_edge(audit_node, node, "RESULTED_IN")
    return node
