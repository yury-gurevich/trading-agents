"""Fault timestamp query helpers.

Agent: kernel
Role: centralize Fault timestamp reads so audits fail loudly on schema drift.
External I/O: GraphStore reads via the injected backend.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

from kernel.fault_graph import FAULT_LABEL, FAULT_SUPPRESSION_LABEL

if TYPE_CHECKING:
    from kernel.graph import GraphStore, Node

FAULT_TIMESTAMP_PROPERTY = "occurred_at"


class MissingFaultTimestampPropertyError(KeyError):
    """Raised when a Fault node lacks the timestamp property audits require."""

    def __init__(self, fault_key: str, property_name: str) -> None:
        """Name the missing timestamp property and the Fault node that lacked it."""
        super().__init__(
            f"Fault {fault_key!r} is missing timestamp property {property_name!r}"
        )


@dataclass(frozen=True)
class FaultOccurrence:
    """One Fault node with its parsed timestamp and collapsed volume."""

    node: Node
    occurred_at: datetime
    occurrence_count: int
    suppressed_count: int


def faults_occurred_in_window(
    graph: GraphStore, start: datetime, *, end: datetime | None = None
) -> tuple[FaultOccurrence, ...]:
    """Return Faults whose required occurrence timestamp falls in the window."""
    return tuple(
        item
        for item in fault_occurrences(graph)
        if item.occurred_at >= start and (end is None or item.occurred_at < end)
    )


def fault_count_in_window(
    graph: GraphStore, start: datetime, *, end: datetime | None = None
) -> int:
    """Count Fault occurrences, including collapsed duplicate volume."""
    return sum(
        item.occurrence_count
        for item in faults_occurred_in_window(graph, start, end=end)
    )


def fault_occurrences(graph: GraphStore) -> tuple[FaultOccurrence, ...]:
    """Return all Fault nodes newest first, raising on missing timestamps."""
    suppressions = _suppression_counts(graph)
    occurrences = (
        _fault_occurrence(node, suppressions.get(node.key, (1, 0)))
        for node in graph.list_nodes(FAULT_LABEL)
    )
    return tuple(sorted(occurrences, key=lambda item: item.occurred_at, reverse=True))


def _fault_occurrence(node: Node, counts: tuple[int, int]) -> FaultOccurrence:
    return FaultOccurrence(
        node=node,
        occurred_at=_fault_timestamp(node),
        occurrence_count=counts[0],
        suppressed_count=counts[1],
    )


def _fault_timestamp(node: Node) -> datetime:
    try:
        raw = node.props[FAULT_TIMESTAMP_PROPERTY]
    except KeyError as exc:
        raise MissingFaultTimestampPropertyError(
            node.key, FAULT_TIMESTAMP_PROPERTY
        ) from exc
    return datetime.fromisoformat(str(raw))


def _suppression_counts(graph: GraphStore) -> dict[str, tuple[int, int]]:
    counts: dict[str, tuple[int, int]] = {}
    for node in graph.list_nodes(FAULT_SUPPRESSION_LABEL):
        if "first_fault_key" not in node.props:
            continue
        counts[str(node.props["first_fault_key"])] = (
            int(node.props.get("occurrence_count", 1)),
            int(node.props.get("suppressed_count", 0)),
        )
    return counts
