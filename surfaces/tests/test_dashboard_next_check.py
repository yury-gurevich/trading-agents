"""Next fleet-check time tests for the dashboard's fleet alert.

Agent: surfaces
Role: prove the alert names the master's next wake, not "about an hour", when asleep.
External I/O: none.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from typing import cast

from surfaces.dashboard import build_app
from surfaces.dashboard.time_windows import next_master_wake
from surfaces.tests.dashboard_fakes import FakeAzureReader
from surfaces.tests.test_dashboard_app import invoke
from surfaces.tests.test_dashboard_costs import _settings
from surfaces.tests.test_dashboard_projections import cascade_graph


def _at(hour: int, minute: int = 0) -> datetime:
    return datetime(2026, 9, 24, hour, minute, tzinfo=UTC)


def test_master_awake_means_no_separate_next_wake() -> None:
    assert next_master_wake(_settings(), _at(22, 0)) is None
    assert next_master_wake(_settings(), _at(0, 10)) is None


def test_master_asleep_names_the_next_window_start() -> None:
    assert next_master_wake(_settings(), _at(2, 3)) == "2026-09-24T20:25:00+00:00"
    assert next_master_wake(_settings(), _at(20, 0)) == "2026-09-24T20:25:00+00:00"


def test_a_five_hour_old_failure_still_shows_with_the_next_wake() -> None:
    now = _at(5, 30)
    graph = cascade_graph("app-run")
    checked_at = (now - timedelta(hours=5)).isoformat(timespec="seconds")
    graph.merge_node(
        "FleetPreflight",
        f"preflight:{checked_at}",
        {"checked_at": checked_at, "passed": False, "failures": ["x:y:z:http_400"]},
    )
    app = build_app(graph, FakeAzureReader(), _settings(), now=now)

    payload = json.loads(invoke(app, "/api/verdict?run=app-run")[2])
    readiness = cast("dict[str, object]", payload["readiness"])

    assert readiness["state"] == "failing"
    assert readiness["checked_at"] == "2026-09-24T00:30:00+00:00"
    assert readiness["next_check"] == "2026-09-24T20:25:00+00:00"


def test_a_same_day_window_rolls_the_next_wake_to_tomorrow() -> None:
    settings = _settings().model_copy(
        update={"master_window_start_utc": "01:00", "window_end_utc": "05:00"}
    )

    assert next_master_wake(settings, _at(6, 0)) == "2026-09-25T01:00:00+00:00"
