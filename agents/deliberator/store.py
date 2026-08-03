"""Deliberator graph read/write path.

Agent: deliberator
Role: find pending PM runs and write append-only deliberation audit artifacts.
External I/O: GraphStore reads and writes via the injected backend.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from contracts.portfolio_manager import OrderIntentSet
    from kernel import GraphStore, Node

PM_RUN_LABEL = "PMRun"
DELIBERATION_RUN_LABEL = "DeliberationRun"
LLM_CALL_LABEL = "LLMCall"
DELIBERATED_EDGE = "DELIBERATED_BY"
PRODUCED_BY_EDGE = "PRODUCED_BY"


def find_pending(graph: GraphStore) -> list[Node]:
    """Return order-carrying PMRun nodes with no DeliberationRun marker yet."""
    pending: list[Node] = []
    for node in graph.list_nodes(PM_RUN_LABEL):
        if "order_intent_set" not in node.props:
            continue
        done = list(graph.descendants(node, max_depth=1, edge_types={DELIBERATED_EDGE}))
        if not done:
            pending.append(node)
    return pending


def write_deliberation_run(
    graph: GraphStore,
    pm_node: Node,
    *,
    order_set: OrderIntentSet,
    verdicts: dict[str, str],
    vetoed_tickers: list[str],
    debates: dict[str, object],
    narrative: str,
    transcript: list[dict[str, object]],
    role_models: dict[str, str],
    max_rounds: int,
    real_debate_count: int,
    failed_open_count: int,
    failed_open_tickers: list[str],
    llm_call_keys: list[str],
) -> Node:
    """Write one idempotent DeliberationRun and link LLM audit calls."""
    key = order_set.run_id
    current = graph.get_node(DELIBERATION_RUN_LABEL, key)
    if current is None:
        current = graph.merge_node(
            DELIBERATION_RUN_LABEL,
            key,
            {
                "source_pm_run_id": order_set.run_id,
                "verdicts": verdicts,
                "vetoed_tickers": vetoed_tickers,
                "debates": debates,
                "narrative": narrative,
                "transcript": transcript,
                "role_models": role_models,
                "max_rounds": max_rounds,
                "real_debate_count": real_debate_count,
                "failed_open_count": failed_open_count,
                "failed_open_tickers": failed_open_tickers,
                "created_at": datetime.now(tz=UTC).isoformat(),
            },
        )
    graph.add_edge(pm_node, current, DELIBERATED_EDGE)
    for call_key in llm_call_keys:
        _link_llm_call(graph, current, call_key)
    return current


def _link_llm_call(graph: GraphStore, run: Node, call_key: str) -> None:
    node = graph.get_node(LLM_CALL_LABEL, call_key)
    if node is not None:
        graph.add_edge(run, node, PRODUCED_BY_EDGE)
