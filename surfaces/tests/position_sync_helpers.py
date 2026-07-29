"""Dashboard test helper for position-sync source runs.

Agent: surfaces
Role: seed the minimal sync marker needed before provider resume.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from contracts.position_sync import POSITION_SYNC_EDGE, POSITION_SYNC_PHASE

if TYPE_CHECKING:
    from kernel import InMemoryGraphStore


def mark_position_synced(graph: InMemoryGraphStore, run_id: str) -> None:
    """Attach a fresh position-sync marker to one RunRequest."""
    run = graph.get_node("RunRequest", f"run-request:{run_id}")
    assert run is not None
    marker = graph.merge_node(
        "MonitorRun",
        f"position-sync:{run_id}",
        {
            "source_run_id": run_id,
            "phase": POSITION_SYNC_PHASE,
            "position_book_status": "fresh",
        },
    )
    graph.add_edge(run, marker, POSITION_SYNC_EDGE)
