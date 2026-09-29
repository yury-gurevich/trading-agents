"""Forecaster entrypoint tests: the deployed graph-pull loop (DL-241 D9).

Agent: forecaster
Role: verify the entrypoint runs a graph-pull loop that fires the barrier claim only
      and that the served bus still answers a request with a shadow-only output (the
      deployed route from the provider's history is in test_barrier_route.py).
External I/O: none.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

import agents.forecaster.entrypoint as ep
from agents.forecaster.entrypoint import build_served_bus
from agents.forecaster.tests.barrier_helpers import (
    RecordingBus,
    barrier_bars,
    deployed_analyst_run,
    seed_history,
)
from agents.forecaster.tests.helpers import forecast_message
from contracts.forecaster import ShadowPrediction
from kernel import InMemoryGraphStore
from kernel.serve_loop import LocalRequestConsumer, serve_once

if TYPE_CHECKING:
    from collections.abc import Callable

    import pytest

    from agents.forecaster.work import ForecasterWorkItem


def test_main_runs_the_graph_pull_loop_with_the_barrier_leg_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """FORE-TRG-01 / FORE-TRG-02: the container polls for an unconsumed, current
    AnalystRun (DL-241 D11: an old run is never claimed) and fires forecast_barrier
    for each buy with both barriers, and none of the three advisory legs; the same
    current run's settlement pass is the loop's second kind of work (S241), and the
    old run gets none."""
    graph = InMemoryGraphStore()
    run = deployed_analyst_run(graph)
    seed_history(
        graph,
        barrier_bars("AAPL", 760) + barrier_bars("GOOG", 760),
        run_key="analyst-run-deployed",
    )
    # The backlog (DL-241 D11): an old run with the same buys and a ready history.
    old = dict(run.props)
    old["created_at"] = (datetime.now(tz=UTC) - timedelta(days=2)).isoformat()
    graph.merge_node("AnalystRun", "analyst-run-old", old)
    seed_history(
        graph,
        barrier_bars("AAPL", 760) + barrier_bars("GOOG", 760),
        run_key="analyst-run-old",
    )
    bus = RecordingBus()
    seen: dict[str, object] = {}

    monkeypatch.setattr(ep, "activate_agent", lambda *args, **kwargs: None)
    monkeypatch.setattr(ep, "master_public_key_from_env", lambda: "pub")
    monkeypatch.setattr(ep, "build_graph_from_env", lambda: graph)
    monkeypatch.setattr(ep, "build_served_bus", lambda graph_arg, sink: bus)

    def fake_work_loop(
        find_pending: Callable[[], list[ForecasterWorkItem]],
        process_one: Callable[[ForecasterWorkItem], None],
        *,
        poll_interval: float,
        graph: object,
        agent: str,
        flush_faults: Callable[[], None],
    ) -> None:
        pending = find_pending()
        seen.update(pending=[(item.kind, item.node.key) for item in pending])
        seen.update(poll=poll_interval, agent=agent)
        seen.update(loop_graph=graph, flush=flush_faults)
        for item in pending:
            process_one(item)
        seen["after"] = len(find_pending())

    monkeypatch.setattr(ep, "work_loop", fake_work_loop)
    monkeypatch.setenv("FORECASTER_POLL_INTERVAL", "11")

    ep.main()

    assert seen["pending"] == [
        ("forecast", "analyst-run-deployed"),
        ("settle", "analyst-run-deployed"),
    ]
    assert seen["after"] == 0
    assert [node.key for node in graph.list_nodes("BarrierSettlementPass")] == [
        "settlement-pass:analyst-run-deployed"
    ]
    assert (seen["poll"], seen["agent"], seen["loop_graph"]) == (
        11,
        "forecaster",
        graph,
    )
    assert callable(seen["flush"])
    fired = [(m.capability, m.payload["subject_ref"]) for m in bus.requests]
    assert fired == [("forecast_barrier", "AAPL"), ("forecast_barrier", "GOOG")]


def test_served_forecast_is_request_triggered_shadow_only() -> None:
    """FORE-TRG-02 / FORE-OUT-02 / FORE-NEV-02: served request writes shadow only."""
    graph = InMemoryGraphStore()
    bus = build_served_bus(graph)
    consumer = LocalRequestConsumer([forecast_message("s99-forecast")])

    served = serve_once(consumer, bus)

    assert served == 1
    assert len(consumer.replies) == 1
    prediction = ShadowPrediction.model_validate(consumer.replies[0].payload)
    assert prediction.shadow is True
    assert len(graph.list_nodes("ShadowPrediction")) == 1
    assert graph.list_nodes("OrderIntent") == ()
    assert graph.list_nodes("PMRun") == ()
    assert graph.list_nodes("CloseDecision") == ()
