"""Sprint 286 A5-A6: deployed held requests and history readiness.

Agent: forecaster
Role: prove the poll sends prices after buys and waits for the held book's bars.
External I/O: none.
"""

from agents.forecaster.poll import (
    DEPLOYED_CAPABILITIES,
    find_pending,
    forecast_analyst_node,
)
from agents.forecaster.tests.barrier_helpers import (
    RecordingBus,
    barrier_bars,
    deployed_analyst_run,
    seed_history,
)
from agents.forecaster.tests.held_helpers import lineage, position, stop
from agents.forecaster.tests.settlement_helpers import seed_run
from contracts.barrier_history import barrier_history_key
from contracts.forecaster import ForecastRequest
from kernel import InMemoryGraphStore


def test_every_held_name_gets_a_claim_request_beside_the_buys() -> None:
    """FORE-TRG-01 / FORE-OUT-09: deployed buys precede one held price request."""
    graph = InMemoryGraphStore()
    bus = RecordingBus()
    run = deployed_analyst_run(graph)
    cop = position(graph)
    lineage(graph, cop)
    stop(graph, cop)

    forecast_analyst_node(run, graph=graph, bus=bus, capabilities=DEPLOYED_CAPABILITIES)

    requests = [ForecastRequest.model_validate(m.payload) for m in bus.requests]
    assert [(r.subject_kind, r.subject_ref) for r in requests] == [
        ("recommendation", "AAPL"),
        ("recommendation", "GOOG"),
        ("position", "COP"),
    ]
    assert requests[-1].features["stop_price"] == 117.08
    assert "stop_pct" not in requests[-1].features
    assert all(r.history_ref == barrier_history_key(run.key) for r in requests)
    assert [m.capability for m in bus.requests] == ["forecast_barrier"] * 3
    [marker] = graph.list_nodes("ForecasterRun")
    assert marker.props["held_count"] == 1


def test_a_run_waits_for_its_bars_while_the_book_holds_a_name() -> None:
    """FORE-TRG-01: even an empty recommendation set waits while COP is held."""
    graph = InMemoryGraphStore()
    run = seed_run(graph, "held-empty-run", lineage=False)
    assert find_pending(graph) == [run]
    position(graph)
    assert find_pending(graph) == []
    seed_history(graph, barrier_bars("COP", 760), run_key=run.key)
    assert find_pending(graph) == [run]
