"""Forecaster poll find_pending tests.

Agent: forecaster
Role: verify the AnalystRun gate — a run is pending until a ForecasterRun is linked
      back via FORECAST_BY, then it is done (idempotent).
External I/O: none.
"""

from __future__ import annotations

from agents.forecaster.poll import (
    ANALYST_RUN_LABEL,
    FORECAST_EDGE,
    FORECASTER_RUN_LABEL,
    find_pending,
)
from kernel import InMemoryGraphStore


def test_unforecast_analyst_run_is_pending() -> None:
    graph = InMemoryGraphStore()
    graph.merge_node(ANALYST_RUN_LABEL, "analyst-run-1", {"recommendation_count": 1})
    pending = find_pending(graph)
    assert [n.key for n in pending] == ["analyst-run-1"]


def test_forecast_analyst_run_is_not_pending() -> None:
    graph = InMemoryGraphStore()
    run = graph.merge_node(ANALYST_RUN_LABEL, "analyst-run-1", {})
    marker = graph.merge_node(FORECASTER_RUN_LABEL, "analyst-run-1", {})
    graph.add_edge(run, marker, FORECAST_EDGE)
    assert find_pending(graph) == []


def test_no_analyst_runs_means_nothing_pending() -> None:
    assert find_pending(InMemoryGraphStore()) == []
