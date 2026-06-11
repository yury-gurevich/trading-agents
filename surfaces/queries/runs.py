"""Dispatcher run read models.

Agent: surfaces
Role: project dispatcher Message lineage into run summaries.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from surfaces.queries._graph import nodes_by_label

if TYPE_CHECKING:
    from kernel import GraphStore, Node

_STEP_ORDER = {
    "scan": 0,
    "analyze": 1,
    "evaluate": 2,
    "submit": 3,
    "check_positions": 4,
    "report": 5,
    "narrative": 6,
}


@dataclass(frozen=True)
class StepRecord:
    """One dispatcher step recorded by the supervisor."""

    name: str
    status: str


@dataclass(frozen=True)
class RunSummary:
    """Surface summary of one dispatcher run."""

    run_id: str
    steps: tuple[StepRecord, ...]
    completed: bool
    message_count: int
    snapshot_available: bool


def recent_runs(graph: GraphStore, limit: int = 10) -> tuple[RunSummary, ...]:
    """Return the most recent dispatcher runs from Message nodes, newest first."""
    summaries = tuple(
        _summary(graph, run_id, nodes) for run_id, nodes in _groups(graph)
    )
    ordered = sorted(
        summaries,
        key=lambda item: _latest_key(graph, item.run_id),
        reverse=True,
    )
    return tuple(ordered[:limit])


def run_detail(graph: GraphStore, run_id: str) -> RunSummary | None:
    """Return one run summary by id, if dispatcher Messages exist for it."""
    nodes = tuple(
        node
        for node in nodes_by_label(graph, "Message")
        if str(node.props.get("run_id", "")) == run_id
    )
    if not nodes:
        return None
    return _summary(graph, run_id, nodes)


def _groups(graph: GraphStore) -> tuple[tuple[str, tuple[Node, ...]], ...]:
    grouped: dict[str, list[Node]] = {}
    for node in nodes_by_label(graph, "Message"):
        run_id = str(node.props.get("run_id", ""))
        if run_id:
            grouped.setdefault(run_id, []).append(node)
    return tuple((run_id, tuple(nodes)) for run_id, nodes in grouped.items())


def _summary(graph: GraphStore, run_id: str, nodes: tuple[Node, ...]) -> RunSummary:
    steps = tuple(
        StepRecord(
            name=str(node.props.get("step", "")),
            status=str(node.props.get("status", "attempted")),
        )
        for node in sorted(nodes, key=_step_order)
    )
    completed = any(step.name == "narrative" for step in steps)
    return RunSummary(
        run_id=run_id,
        steps=steps,
        completed=completed,
        message_count=len(nodes),
        snapshot_available=graph.get_node("Snapshot", f"snapshot:{run_id}") is not None,
    )


def _step_order(node: Node) -> tuple[int, str]:
    name = str(node.props.get("step", ""))
    return (_STEP_ORDER.get(name, len(_STEP_ORDER)), name)


def _latest_key(graph: GraphStore, run_id: str) -> str:
    nodes = tuple(
        node
        for node in nodes_by_label(graph, "Message")
        if str(node.props.get("run_id", "")) == run_id
    )
    return max(str(node.props.get("created_at", node.key)) for node in nodes)
