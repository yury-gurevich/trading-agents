"""R1 dashboard tests for repeated scheduled-run holds.

Agent: surfaces
Role: prove a repeat hold remains visible and explains unknown readiness.
External I/O: none.
"""

from __future__ import annotations

import json
import re
from datetime import UTC, date, datetime, timedelta
from typing import TYPE_CHECKING, cast

from orchestration.fleet_readiness import is_active_run_hold
from orchestration.scheduled_dispatch_gate import hold_unready_run
from surfaces.dashboard import build_app
from surfaces.tests.dashboard_fakes import FakeAzureReader
from surfaces.tests.test_dashboard_app import invoke
from surfaces.tests.test_dashboard_costs import _settings
from surfaces.tests.test_dashboard_projections import cascade_graph

if TYPE_CHECKING:
    from kernel import InMemoryGraphStore
    from orchestration.scheduled_dispatch_gate import DispatchHold

_NOW = datetime(2026, 9, 20, 22, 30, tzinfo=UTC)
_AS_OF = date(2026, 9, 20)
_RUN_ID = "sched-2026-09-20"


def _payload(graph: InMemoryGraphStore, *, now: datetime) -> dict[str, object]:
    app = build_app(graph, FakeAzureReader(), _settings(), now=now)
    return cast(
        "dict[str, object]", json.loads(invoke(app, "/api/verdict?run=app-run")[2])
    )


def _preflight(
    graph: InMemoryGraphStore,
    *,
    key: str,
    checked_at: datetime,
    passed: bool,
    failures: tuple[str, ...] = (),
) -> None:
    graph.merge_node(
        "FleetPreflight",
        key,
        {
            "checked_at": checked_at.isoformat(timespec="seconds"),
            "passed": passed,
            "failure_count": len(failures),
            "failures": list(failures),
            "agent_types_checked": ["scanner"],
        },
    )


def _hold(graph: InMemoryGraphStore, *, now: datetime) -> DispatchHold | None:
    return hold_unready_run(
        graph,
        run_id=_RUN_ID,
        as_of=_AS_OF,
        now=now,
        max_age_minutes=70,
    )


def test_rehold_after_release_creates_active_hold_with_new_evidence() -> None:
    """DRIFT-068: a released hold cannot suppress a later failing hold."""

    graph = cascade_graph("app-run")
    _preflight(
        graph,
        key="preflight:first-failure",
        checked_at=_NOW - timedelta(minutes=5),
        passed=False,
        failures=("unrecoverable:provider:fmp:http_402",),
    )
    assert _hold(graph, now=_NOW) is not None

    recovered_at = _NOW + timedelta(minutes=60)
    _preflight(
        graph,
        key="preflight:recovered",
        checked_at=recovered_at - timedelta(minutes=5),
        passed=True,
    )
    assert _hold(graph, now=recovered_at) is None

    reheld_at = recovered_at + timedelta(minutes=5)
    new_failures = ("transient:master:vault:Timeout",)
    _preflight(
        graph,
        key="preflight:second-failure",
        checked_at=reheld_at - timedelta(minutes=5),
        passed=False,
        failures=new_failures,
    )

    rehold = _hold(graph, now=reheld_at)

    assert rehold is not None
    assert rehold.node_key == "hold:sched-2026-09-20:1"
    holds = graph.list_nodes("RunHold")
    assert len(holds) == 2
    latest = next(hold for hold in holds if hold.key == rehold.node_key)
    assert is_active_run_hold(latest) is True
    assert latest.props["readiness_state"] == "failing"
    assert tuple(latest.props["failures"]) == new_failures
    readiness = cast("dict[str, object]", _payload(graph, now=reheld_at)["readiness"])
    assert readiness["state"] == "held"


def test_stale_check_after_release_keeps_the_hold_visible() -> None:
    """DRIFT-068: a stale check after release creates a visible unknown hold."""

    graph = cascade_graph("app-run")
    _preflight(
        graph,
        key="preflight:first-failure",
        checked_at=_NOW - timedelta(minutes=5),
        passed=False,
    )
    assert _hold(graph, now=_NOW) is not None

    recovered_at = _NOW + timedelta(minutes=60)
    _preflight(
        graph,
        key="preflight:recovered",
        checked_at=recovered_at - timedelta(minutes=5),
        passed=True,
    )
    assert _hold(graph, now=recovered_at) is None

    stale_at = recovered_at + timedelta(minutes=120)
    rehold = _hold(graph, now=stale_at)
    payload = _payload(graph, now=stale_at)

    assert rehold is not None
    assert rehold.state == "unknown"
    assert "readiness" in payload
    assert rehold.node_key == "hold:sched-2026-09-20:1"
    assert cast("dict[str, object]", payload["readiness"])["state"] == "held"


def test_held_run_with_no_check_names_missing_fleet_check() -> None:
    """DRIFT-068: an unknown readiness hold explains missing fleet evidence plainly."""

    graph = cascade_graph("app-run")
    assert _hold(graph, now=_NOW) is not None

    readiness = cast("dict[str, object]", _payload(graph, now=_NOW)["readiness"])
    summary = str(readiness["summary"])

    assert "0 check(s)" not in summary
    assert "no recent fleet check" in summary
    assert not re.search(r"S\d{3}|DL-\d+|MST-", summary)
