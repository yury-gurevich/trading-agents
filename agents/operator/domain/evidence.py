"""Operator graph evidence retrieval.

Agent: operator
Role: collect bounded graph evidence for explanation prompts.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kernel import GraphStore, Node

TRADE_LABELS = {"Recommendation", "OrderIntent", "Fill", "Position", "CloseDecision"}
STATUS_LABELS = {"Snapshot", "MonitorRun", "PMRun"}


def gather_evidence(
    graph: GraphStore, subject: str, max_nodes: int
) -> list[dict[str, object]]:
    """Return matching graph nodes as prompt-safe evidence dictionaries."""
    subject_upper = subject.upper()
    wants_status = "status" in subject.lower() or "system" in subject.lower()
    rows: list[dict[str, object]] = []
    for node in _all_nodes(graph):
        if _matches(node, subject_upper, wants_status):
            rows.append(
                {
                    "label": node.label,
                    "key": node.key,
                    "props": dict(node.props),
                }
            )
        if len(rows) >= max_nodes:
            break
    return rows


def _all_nodes(graph: GraphStore) -> tuple[Node, ...]:
    nodes: list[Node] = []
    for label in sorted(TRADE_LABELS | STATUS_LABELS):
        try:
            nodes.extend(graph.list_nodes(label))
        except AttributeError:
            return ()
    return tuple(nodes)


def _matches(node: Node, subject_upper: str, wants_status: bool) -> bool:
    if wants_status and node.label in STATUS_LABELS:
        return True
    ticker = str(node.props.get("ticker", "")).upper()
    return node.label in TRADE_LABELS and bool(ticker) and ticker in subject_upper
