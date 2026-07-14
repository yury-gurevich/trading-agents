"""Operator graph evidence retrieval.

Agent: operator
Role: collect bounded graph evidence for explanation prompts.
External I/O: none.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kernel import GraphStore, Node

TRADE_LABELS = {"Recommendation", "OrderIntent", "Fill", "Position", "CloseDecision"}
STATUS_LABELS = {"Snapshot", "MonitorRun", "PMRun"}
_RUN_CHAIN = (
    ("INGESTED_BY", "MarketData"),
    ("SCANNED_BY", "ScanRun"),
    ("ANALYZED_BY", "AnalystRun"),
    ("EVALUATED_BY", "PMRun"),
    ("EXECUTED_BY", "ExecutionRun"),
    ("MONITORED_BY", "MonitorRun"),
    ("REPORTED_BY", "Snapshot"),
)


def gather_evidence(
    graph: GraphStore, subject: str, max_nodes: int
) -> list[dict[str, object]]:
    """Return matching graph nodes as prompt-safe evidence dictionaries."""
    subject_upper = subject.upper()
    wants_status = "status" in subject.lower() or "system" in subject.lower()
    rows = _run_evidence(graph, subject)
    if len(rows) >= max_nodes:
        return rows[:max_nodes]
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


def _run_evidence(graph: GraphStore, subject: str) -> list[dict[str, object]]:
    try:
        requests = graph.list_nodes("RunRequest")
    except AttributeError:
        return []
    request = next(
        (node for node in requests if str(node.props.get("run_id", "")) in subject),
        None,
    )
    if request is None:
        return []
    nodes = [request]
    current = request
    for edge, label in _RUN_CHAIN:
        child = next(
            (
                node
                for node in graph.descendants(current, max_depth=1, edge_types={edge})
                if node.label == label
            ),
            None,
        )
        if child is None:
            break
        nodes.append(child)
        current = child
    rows: list[dict[str, object]] = [
        {
            "label": node.label,
            "key": node.key,
            "props": _compact_mapping(node.props),
        }
        for node in nodes
    ]
    rows.extend(_pending_flags(graph))
    return rows


def _pending_flags(graph: GraphStore) -> list[dict[str, object]]:
    """Include outstanding operator attention in any selected-run explanation."""
    try:
        flags = graph.list_nodes("Flag")
    except AttributeError:
        return []
    return [
        {
            "label": node.label,
            "key": node.key,
            "props": _compact_mapping(node.props),
        }
        for node in flags
        if str(node.props.get("status", "")) == "pending"
    ]


def _compact_mapping(value: Mapping[str, object]) -> dict[str, object]:
    return {str(key): _compact(item) for key, item in value.items()}


def _compact(value: object) -> object:
    if isinstance(value, Mapping):
        return _compact_mapping(value)
    if isinstance(value, (list, tuple)):
        if len(value) <= 10 and all(
            isinstance(item, str | int | float | bool) for item in value
        ):
            return list(value)
        return {"item_count": len(value)}
    if isinstance(value, str | int | float | bool) or value is None:
        return value
    return str(value)


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
