"""Run selection helpers shared by dashboard read routes.

Agent: surfaces
Role: resolve the selected graph-pull run without changing graph state.
External I/O: reads the injected GraphStore.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from surfaces.dashboard import projections

if TYPE_CHECKING:
    from kernel import GraphStore


def run_day(graph: GraphStore, query: dict[str, list[str]]) -> str:
    """Resolve the selected run's day from its RunRequest, or empty."""
    run_id = query.get("run", [""])[0]
    node = projections.run_request_node(graph, run_id) if run_id else None
    return str(node.props.get("requested_at", ""))[:10] if node else ""


def selected_run(graph: GraphStore, query: dict[str, list[str]]) -> str:
    """Return a supplied run id or the current latest run id."""
    supplied = query.get("run_id", [""])[0]
    return supplied or projections.latest_run_id(graph)
