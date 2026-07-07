"""Scheduled dispatcher decision tests.

Agent: orchestration
Role: prove cron placement is calendar-gated, day-keyed, and merge-idempotent.
External I/O: none.
"""

from __future__ import annotations

from datetime import date

import pytest

from agents.scanner.universe import FakeUniverse
from contracts.provider import RUN_REQUEST_LABEL
from kernel import InMemoryGraphStore
from orchestration.scheduled_dispatch import (
    CalendarWindowExceededError,
    decide_scheduled_run,
    place_scheduled_run,
    scheduled_run_id,
)
from orchestration.settings import OrchestratorSettings


def test_trading_day_places_day_keyed_run_request() -> None:
    graph = InMemoryGraphStore()

    result = place_scheduled_run(graph, as_of=date(2026, 7, 8))

    assert result.action == "placed"
    assert result.run_id == "sched-2026-07-08"
    assert result.node_key == "run-request:sched-2026-07-08"
    assert result.tickers == ("AAPL", "MSFT", "NVDA", "SPY")
    node = graph.get_node(RUN_REQUEST_LABEL, result.node_key)
    assert node is not None
    assert node.props["run_id"] == result.run_id
    assert node.props["requested_at"] == "2026-07-08"


def test_weekend_and_holiday_skip_with_stated_reason() -> None:
    weekend = decide_scheduled_run(date(2026, 7, 4))
    holiday_graph = InMemoryGraphStore()

    holiday = place_scheduled_run(holiday_graph, as_of=date(2026, 7, 3))

    assert weekend.action == "skip"
    assert weekend.run_id == "sched-2026-07-04"
    assert "not a NYSE trading session" in weekend.reason
    assert holiday.action == "skipped"
    assert holiday.run_id == "sched-2026-07-03"
    assert "not a NYSE trading session" in holiday.reason
    assert holiday_graph.list_nodes(RUN_REQUEST_LABEL) == ()


def test_double_fire_merges_to_one_run_request_node() -> None:
    graph = InMemoryGraphStore()

    first = place_scheduled_run(graph, as_of=date(2026, 7, 8))
    second = place_scheduled_run(graph, as_of=date(2026, 7, 8))

    assert first.node_key == second.node_key
    nodes = graph.list_nodes(RUN_REQUEST_LABEL)
    assert len(nodes) == 1
    assert nodes[0].key == "run-request:sched-2026-07-08"


def test_calendar_window_exceeded_raises_explicit_error() -> None:
    with pytest.raises(CalendarWindowExceededError, match="beyond the NYSE calendar"):
        decide_scheduled_run(date(2028, 1, 3))


def test_empty_configured_universe_is_an_error() -> None:
    graph = InMemoryGraphStore()
    settings = OrchestratorSettings(universe="empty")

    with pytest.raises(ValueError, match="has no tickers"):
        place_scheduled_run(
            graph,
            as_of=date(2026, 7, 8),
            settings=settings,
            universe_source=FakeUniverse({"empty": ()}),
        )


def test_scheduled_run_id_is_stable() -> None:
    assert scheduled_run_id(date(2026, 7, 8)) == "sched-2026-07-08"
