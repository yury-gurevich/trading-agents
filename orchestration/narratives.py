"""Dispatcher narrative step helper.

Agent: orchestration
Role: run reporter narratives for positions opened by one PM run.
External I/O: none; uses injected graph and message bus ports.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from orchestration.lineage import position_ids_for_run
from orchestration.steps import step_narrative

if TYPE_CHECKING:
    from kernel import FaultSink, GraphStore, MessageBus


def write_narratives(
    bus: MessageBus,
    graph: GraphStore,
    pm_run_id: str,
    sink: FaultSink | None,
) -> bool:
    """Write trade narratives for all positions opened by one PM run."""
    stories = [
        step_narrative(bus, position_id, sink)
        for position_id in position_ids_for_run(graph, pm_run_id)
    ]
    return bool(stories) and all(story is not None for story in stories)
