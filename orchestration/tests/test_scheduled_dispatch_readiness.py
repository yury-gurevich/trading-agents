"""Readiness-gated scheduled dispatcher tests.

Agent: orchestration
Role: prove a scheduled run is placed only for a fresh ready fleet.
External I/O: none.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from importlib import import_module

from agents.scanner.universe import FakeUniverse
from contracts.provider import RUN_REQUEST_LABEL
from kernel import InMemoryGraphStore
from orchestration.fleet_readiness import is_active_run_hold
from orchestration.scheduled_dispatch import (
    ScheduledDispatchResult,
    place_scheduled_run,
)

_NOW = datetime(2026, 9, 20, 22, 30, tzinfo=UTC)
_AS_OF = date(2026, 7, 8)


def _preflight(
    graph: InMemoryGraphStore,
    *,
    checked_at: datetime,
    passed: bool,
    failures: tuple[str, ...] = (),
) -> None:
    checked = checked_at.isoformat(timespec="seconds")
    graph.merge_node(
        "FleetPreflight",
        f"preflight:{checked}",
        {"checked_at": checked, "passed": passed, "failures": list(failures)},
    )


def _place(graph: InMemoryGraphStore) -> ScheduledDispatchResult:
    return place_scheduled_run(
        graph,
        as_of=_AS_OF,
        now=_NOW,
        universe_source=FakeUniverse({"sp500": ("AAPL",)}),
    )


def test_failing_fleet_holds_run_and_records_both_failures() -> None:
    graph = InMemoryGraphStore()
    failures = ("unrecoverable:provider:fmp:http_402", "transient:master:vault:Timeout")
    _preflight(
        graph, checked_at=_NOW - timedelta(minutes=5), passed=False, failures=failures
    )

    result = _place(graph)

    assert result.action == "held"
    assert result.readiness_state == "failing"
    assert result.failures == failures
    assert graph.list_nodes(RUN_REQUEST_LABEL) == ()
    (hold,) = graph.list_nodes("RunHold")
    assert hold.key == "hold:sched-2026-07-08"
    assert hold.props["state"] == "held"
    assert hold.props["readiness_state"] == "failing"
    assert tuple(hold.props["failures"]) == failures


def test_absent_preflight_holds_with_unknown_readiness() -> None:
    graph = InMemoryGraphStore()

    result = _place(graph)

    assert result.action == "held"
    assert result.readiness_state == "unknown"
    (hold,) = graph.list_nodes("RunHold")
    assert hold.props["preflight_key"] == ""


def test_stale_passing_preflight_holds_as_unknown() -> None:
    graph = InMemoryGraphStore()
    _preflight(graph, checked_at=_NOW - timedelta(minutes=71), passed=True)

    result = _place(graph)

    assert result.action == "held"
    assert result.readiness_state == "unknown"


def test_latest_preflight_wins_over_an_older_failure() -> None:
    graph = InMemoryGraphStore()
    _preflight(
        graph,
        checked_at=_NOW - timedelta(minutes=20),
        passed=False,
        failures=("transient:provider:feed:Timeout",),
    )
    _preflight(graph, checked_at=_NOW - timedelta(minutes=5), passed=True)

    result = _place(graph)

    assert result.action == "placed"
    assert graph.list_nodes("RunHold") == ()


def test_invalid_or_out_of_order_preflight_facts_do_not_displace_latest() -> None:
    graph = InMemoryGraphStore()
    _preflight(graph, checked_at=_NOW - timedelta(minutes=5), passed=True)
    graph.merge_node(
        "FleetPreflight",
        "preflight:older",
        {"checked_at": (_NOW - timedelta(minutes=10)).isoformat(), "passed": False},
    )
    graph.merge_node(
        "FleetPreflight",
        "preflight:invalid",
        {"checked_at": "not-a-timestamp", "passed": False},
    )
    graph.merge_node(
        "FleetPreflight",
        "preflight:non-string",
        {"checked_at": 42, "passed": False},
    )

    result = _place(graph)

    assert result.action == "placed"


def test_failing_refire_merges_one_hold() -> None:
    graph = InMemoryGraphStore()
    _preflight(
        graph,
        checked_at=_NOW - timedelta(minutes=5),
        passed=False,
    )

    first = _place(graph)
    second = _place(graph)

    assert (first.action, second.action) == ("held", "held")
    assert len(graph.list_nodes("RunHold")) == 1


def test_recovery_releases_hold_and_places_run() -> None:
    graph = InMemoryGraphStore()
    _preflight(graph, checked_at=_NOW - timedelta(minutes=5), passed=False)
    _place(graph)
    _preflight(graph, checked_at=_NOW - timedelta(minutes=1), passed=True)

    recovered = _place(graph)

    assert recovered.action == "placed"
    (hold,) = graph.list_nodes("RunHold")
    assert hold.props["state"] == "held"
    assert "released_at" in hold.props
    assert is_active_run_hold(hold) is False


def test_calendar_skip_writes_no_hold_when_fleet_is_failing() -> None:
    graph = InMemoryGraphStore()
    _preflight(graph, checked_at=_NOW - timedelta(minutes=5), passed=False)

    result = place_scheduled_run(graph, as_of=date(2026, 7, 4), now=_NOW)

    assert result.action == "skipped"
    assert graph.list_nodes("RunHold") == ()


def test_readiness_reader_never_writes_master_owned_preflight() -> None:
    """MST-IDN-02: orchestration reads but never writes FleetPreflight evidence."""

    class SpyGraph:
        def __init__(self) -> None:
            self.write_calls = 0

        def list_nodes(self, _label: str) -> tuple[object, ...]:
            return ()

        def merge_node(self, *_args: object, **_kwargs: object) -> None:
            self.write_calls += 1

    graph = SpyGraph()
    module = import_module("orchestration.fleet_readiness")

    readiness = module.fleet_readiness(graph, now=_NOW, max_age_minutes=70)

    assert readiness.state == "unknown"
    assert graph.write_calls == 0
