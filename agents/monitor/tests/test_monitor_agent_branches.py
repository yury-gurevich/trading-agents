"""MonitorAgent defensive branch tests.

Agent: monitor
Role: exercise degraded branches that provider validation usually prevents.
External I/O: none.
"""

from __future__ import annotations

from agents.monitor import MonitorAgent
from agents.monitor.domain.positions import position_from_fill
from agents.monitor.store import open_position
from agents.monitor.tests.helpers import seed_fill
from kernel import CollectingFaultSink, InMemoryGraphStore, InProcessBus


def test_missing_price_in_nonempty_price_map_records_fault() -> None:
    bus = InProcessBus()
    graph = InMemoryGraphStore()
    sink = CollectingFaultSink()
    agent = MonitorAgent(bus, graph=graph, sink=sink)
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

    decisions = agent._evaluate_positions(
        "monitor-run-fixture", (position,), {"MSFT": 10000}
    )

    assert decisions == ()
    assert len(sink.faults) == 1
