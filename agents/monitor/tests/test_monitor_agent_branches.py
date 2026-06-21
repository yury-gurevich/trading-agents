"""MonitorAgent defensive branch tests.

Agent: monitor
Role: exercise degraded branches that provider validation usually prevents.
External I/O: none.
"""

from __future__ import annotations

from agents.monitor.domain.positions import position_from_fill
from agents.monitor.run import _evaluate_positions
from agents.monitor.store import open_position
from agents.monitor.tests.helpers import seed_fill
from kernel import CollectingFaultSink, InMemoryGraphStore


def test_missing_price_in_nonempty_price_map_records_fault() -> None:
    graph = InMemoryGraphStore()
    sink = CollectingFaultSink()
    seed_fill(graph)
    fill = graph.get_node("Fill", "pm-run-fixture:AAPL:buy")
    assert fill is not None
    draft = position_from_fill(
        graph,
        run_id="pm-run-fixture",
        fill=fill,
        default_stop_pct=0.05,
        default_target_pct=0.10,
        default_horizon_days=14,
    )
    position = open_position(graph, draft, fill)

    decisions = _evaluate_positions(
        graph, sink, "monitor-run-fixture", (position,), {"MSFT": 10000}
    )

    assert decisions == ()
    assert len(sink.faults) == 1
