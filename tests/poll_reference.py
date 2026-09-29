"""The seven pre-S242 pending finders, kept verbatim as an oracle (S242 A5).

Agent: tooling
Role: list-then-walk reference implementations of each graph-pull poll's pending
      set, so a test can hold the key-and-edge versions to the same set and order.
External I/O: none (reads the injected GraphStore).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.analyst.poll import _book_sync_attempted
from agents.provider.barrier_history import _qualifying_tickers
from contracts.barrier_history import is_current_run
from contracts.position_sync import POSITION_SYNC_PHASE

if TYPE_CHECKING:
    from collections.abc import Callable
    from datetime import datetime

    from kernel import GraphStore, Node


def _unprocessed(graph: GraphStore, label: str, edge: str) -> list[Node]:
    return [
        node
        for node in graph.list_nodes(label)
        if not list(graph.descendants(node, max_depth=1, edge_types={edge}))
    ]


def analyst(graph: GraphStore) -> list[Node]:
    """ScanRuns with no AnalystRun whose book sync was attempted."""
    return [
        node
        for node in _unprocessed(graph, "ScanRun", "ANALYZED_BY")
        if _book_sync_attempted(graph, node)
    ]


def reporter(graph: GraphStore) -> list[Node]:
    """MonitorRuns that are not sync markers and have no Snapshot."""
    return [
        node
        for node in graph.list_nodes("MonitorRun")
        if node.props.get("phase") != POSITION_SYNC_PHASE
        and not list(graph.descendants(node, max_depth=1, edge_types={"REPORTED_BY"}))
    ]


def barrier(graph: GraphStore, now: datetime) -> list[Node]:
    """Current AnalystRuns with a qualifying buy and no BarrierHistory."""
    return [
        node
        for node in _unprocessed(graph, "AnalystRun", "BARRIER_HISTORY_BY")
        if is_current_run(node.props, now) and _qualifying_tickers(node)
    ]


def simple(label: str, edge: str) -> Callable[[GraphStore], list[Node]]:
    """The provider, scanner, PM and monitor shape: no processed edge."""
    return lambda graph: _unprocessed(graph, label, edge)
