"""Analyst test helper for the S147 sync precondition.

Agent: analyst
Role: seed the run-level sync marker required before graph-pull analysis.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from contracts.position_sync import (
    POSITION_SYNC_EDGE,
    POSITION_SYNC_PHASE,
    RUN_REQUEST_LABEL,
    run_request_key,
)

if TYPE_CHECKING:
    from kernel import InMemoryGraphStore


def mark_book_synced(
    graph: InMemoryGraphStore,
    run_id: str,
    *,
    status: Literal["fresh", "stale"] = "fresh",
) -> None:
    request = graph.merge_node(
        RUN_REQUEST_LABEL,
        run_request_key(run_id),
        {"run_id": run_id, "tickers": ("AAPL", "MSFT")},
    )
    marker = graph.merge_node(
        "MonitorRun",
        f"position-sync:{run_id}",
        {"phase": POSITION_SYNC_PHASE, "position_book_status": status},
    )
    graph.add_edge(request, marker, POSITION_SYNC_EDGE)
