"""P4 dispatcher parity test on Celery eager mode.

Agent: orchestration
Role: prove the daily loop works over the distributed bus path without infra.
External I/O: none; Celery uses eager in-memory settings.
"""

from __future__ import annotations

from agents.execution.broker import PaperBroker
from kernel import CeleryBus, CeleryBusSettings, InMemoryGraphStore
from orchestration import Dispatcher
from orchestration.tests.helpers import (
    fixture_universe,
    node_count,
    source,
    trigger,
)


def test_p4_celery_eager_parity() -> None:
    graph = InMemoryGraphStore()
    bus = CeleryBus(
        settings=CeleryBusSettings(
            celery_task_always_eager=True,
            celery_task_eager_propagates=False,
        )
    )
    result = Dispatcher(
        bus,
        graph,
        source=source(),
        broker=PaperBroker(),
        universe_source=fixture_universe(),
    ).execute_run(trigger("p4-celery-parity"))
    assert result.completed is True
    assert result.snapshot is not None
    assert result.snapshot.portfolio_metrics["positions_opened"] >= 1
    assert result.snapshot.portfolio_metrics["positions_closed"] >= 1
    assert node_count(graph, "Snapshot") == 1
    assert node_count(graph, "TradeNarrative") == 1
    assert node_count(graph, "Message") >= 1
