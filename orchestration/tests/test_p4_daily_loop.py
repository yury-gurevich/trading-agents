"""P4 daily-loop dispatcher test on the in-process bus.

Agent: orchestration
Role: prove Dispatcher drives the seven-agent paper loop from one trigger.
External I/O: none.
"""

from __future__ import annotations

from agents.execution.broker import PaperBroker
from kernel import InMemoryGraphStore, InProcessBus
from orchestration import Dispatcher
from orchestration.tests.helpers import (
    fixture_universe,
    node_count,
    source,
    trigger,
)


def test_p4_daily_loop_on_in_process_bus() -> None:
    graph = InMemoryGraphStore()
    result = Dispatcher(
        InProcessBus(),
        graph,
        source=source(),
        broker=PaperBroker(),
        universe_source=fixture_universe(),
    ).execute_run(trigger("p4-daily-loop"))
    assert result.completed is True
    assert result.snapshot is not None
    assert result.snapshot.portfolio_metrics["positions_opened"] >= 1
    assert result.snapshot.portfolio_metrics["positions_closed"] >= 1
    assert node_count(graph, "Snapshot") == 1
    assert node_count(graph, "TradeNarrative") == 1
