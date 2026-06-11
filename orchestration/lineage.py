"""Orchestration lineage lookup helpers.

Agent: orchestration
Role: query graph lineage needed by dispatcher follow-up steps.
External I/O: GraphStore reads via the injected backend.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kernel import GraphStore, Node


def position_ids_for_run(graph: GraphStore, pm_run_id: str) -> tuple[str, ...]:
    """Return position ids opened by fills from one PM run."""
    pm_run = graph.get_node("PMRun", pm_run_id)
    if pm_run is None:
        return ()
    positions: dict[str, Node] = {}
    for order in graph.ancestors(pm_run, max_depth=1, edge_types={"EMITTED_BY"}):
        for fill in graph.ancestors(order, max_depth=1, edge_types={"EXECUTES"}):
            for position in graph.descendants(fill, max_depth=1, edge_types={"OPENS"}):
                positions[position.key] = position
    return tuple(positions)
