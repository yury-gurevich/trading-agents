"""Position-sync display branch tests.

Agent: orchestration
Role: prove stale broker-book reasons appear in trace and observatory views.
External I/O: stdout only in captured tests.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from contracts.position_sync import POSITION_SYNC_EDGE, POSITION_SYNC_PHASE
from kernel import InMemoryGraphStore
from orchestration.batch_trace import print_trace
from orchestration.packs.trading_observatory import inspect
from orchestration.start import place_run_request

if TYPE_CHECKING:
    import pytest


def test_stale_position_sync_reason_is_visible(
    capsys: pytest.CaptureFixture[str],
) -> None:
    graph = InMemoryGraphStore()
    place_run_request(graph, run_id="stale-display", tickers=("AAPL",))
    run = graph.get_node("RunRequest", "run-request:stale-display")
    assert run is not None
    marker = graph.merge_node(
        "MonitorRun",
        "position-sync:stale-display",
        {
            "source_run_id": "stale-display",
            "phase": POSITION_SYNC_PHASE,
            "position_book_status": "stale",
            "snapshot_key": "snapshot:stale-display",
            "position_book_stale_reason": "broker unavailable",
        },
    )
    graph.add_edge(run, marker, POSITION_SYNC_EDGE)

    assert print_trace(graph, "stale-display") == 1
    assert "stale_reason=broker unavailable" in capsys.readouterr().out
    assert "stale_reason=broker unavailable" in inspect(graph, "stale-display")
