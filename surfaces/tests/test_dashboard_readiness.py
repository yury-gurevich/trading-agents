"""Dashboard readiness-override tests.

Agent: surfaces
Role: show held or failing fleet readiness in the master verdict.
External I/O: none.
"""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, cast

from surfaces.dashboard import build_app
from surfaces.dashboard.projections_readiness import _failures
from surfaces.tests.dashboard_fakes import FakeAzureReader
from surfaces.tests.test_dashboard_app import invoke
from surfaces.tests.test_dashboard_costs import _settings
from surfaces.tests.test_dashboard_projections import cascade_graph

if TYPE_CHECKING:
    from kernel import InMemoryGraphStore

_NOW = datetime(2026, 9, 20, 22, 30, tzinfo=UTC)


def _payload(graph: InMemoryGraphStore) -> dict[str, object]:
    app = build_app(graph, FakeAzureReader(), _settings(), now=_NOW)
    return cast(
        "dict[str, object]", json.loads(invoke(app, "/api/verdict?run=app-run")[2])
    )


def _held_graph() -> InMemoryGraphStore:
    graph = cascade_graph("app-run")
    graph.merge_node(
        "RunHold",
        "hold:sched-2026-09-20",
        {
            "as_of": "2026-09-20",
            "state": "held",
            "failures": [
                "unrecoverable:provider:fmp:unrecoverable:http_402",
                "transient:master:vault:TimeoutError",
            ],
        },
    )
    return graph


def _failed_graph() -> InMemoryGraphStore:
    graph = cascade_graph("app-run")
    checked_at = (_NOW - timedelta(minutes=30)).isoformat(timespec="seconds")
    graph.merge_node(
        "FleetPreflight",
        f"preflight:{checked_at}",
        {
            "checked_at": checked_at,
            "passed": False,
            "failures": ["unrecoverable:provider:fmp:unrecoverable:http_402"],
        },
    )
    return graph


def test_held_run_forces_red_dashboard_readiness_verdict() -> None:
    payload = _payload(_held_graph())

    assert payload["light"] == "RED"
    assert str(payload["summary"]).startswith(
        "Tonight's run is held: 2 check(s) failing"
    )
    assert payload["readiness"] == {
        "state": "held",
        "summary": payload["summary"],
        "failures": [
            "unrecoverable:provider:fmp:unrecoverable:http_402",
            "transient:master:vault:TimeoutError",
        ],
    }


def test_recent_failing_preflight_forces_red_dashboard_readiness_verdict() -> None:
    payload = _payload(_failed_graph())

    assert payload["light"] == "RED"
    assert str(payload["summary"]).startswith("Fleet check failing (1)")
    assert payload["readiness"] == {
        "state": "failing",
        "summary": payload["summary"],
        "failures": ["unrecoverable:provider:fmp:unrecoverable:http_402"],
    }


def test_passing_preflight_leaves_existing_verdict_payload_unchanged() -> None:
    baseline = _payload(cascade_graph("app-run"))
    graph = cascade_graph("app-run")
    checked_at = (_NOW - timedelta(minutes=5)).isoformat(timespec="seconds")
    graph.merge_node(
        "FleetPreflight",
        f"preflight:{checked_at}",
        {"checked_at": checked_at, "passed": True, "failures": []},
    )

    payload = _payload(graph)

    assert payload == baseline
    assert "readiness" not in payload


def test_released_hold_leaves_existing_verdict_payload_unchanged() -> None:
    baseline = _payload(cascade_graph("app-run"))
    graph = _held_graph()
    graph.merge_node(
        "RunHold",
        "hold:sched-2026-09-20",
        {"released_at": "2026-09-20T22:29:00+00:00"},
    )

    payload = _payload(graph)

    assert payload == baseline
    assert "readiness" not in payload


def test_held_run_without_failure_list_uses_a_safe_summary() -> None:
    graph = cascade_graph("app-run")
    graph.merge_node(
        "RunHold",
        "hold:sched-2026-09-20",
        {"as_of": "2026-09-20", "state": "held", "failures": "unavailable"},
    )

    payload = _payload(graph)

    assert payload["readiness"] == {
        "state": "held",
        "summary": (
            "Tonight's run is held: 0 check(s) failing — no failure detail recorded"
        ),
        "failures": [],
    }


def test_failure_helper_handles_non_mapping_properties() -> None:
    assert _failures(object()) == ()


def test_readiness_summary_has_no_sprint_law_or_design_identifiers() -> None:
    summaries = (
        _payload(_held_graph())["summary"],
        _payload(_failed_graph())["summary"],
    )

    assert all(
        not re.search(r"S\d{3}|DL-\d+|MST-", str(summary)) for summary in summaries
    )
