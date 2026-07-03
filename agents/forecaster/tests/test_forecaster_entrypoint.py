"""Forecaster served-entrypoint tests.

Agent: forecaster
Role: verify request-triggered serving writes only advisory shadow artifacts.
External I/O: none.
"""

from __future__ import annotations

from agents.forecaster.entrypoint import build_served_bus
from agents.forecaster.tests.helpers import forecast_message
from contracts.forecaster import ShadowPrediction
from kernel import InMemoryGraphStore
from kernel.serve_loop import LocalRequestConsumer, serve_once


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
