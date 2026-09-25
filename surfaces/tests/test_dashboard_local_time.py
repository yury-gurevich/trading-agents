"""The dashboard shows the operator's own time and names agents the check refused.

Agent: surfaces
Role: prove window labels, the page's zone, and refused-agent rows.
External I/O: none.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from typing import Any, cast

from kernel import InMemoryGraphStore
from orchestration.start import place_run_request
from surfaces.dashboard import build_app
from surfaces.dashboard.projections_fleet import fleet_projection
from surfaces.dashboard.time_windows import window_label
from surfaces.tests.dashboard_fakes import FakeAzureReader
from surfaces.tests.test_dashboard_app import invoke
from surfaces.tests.test_dashboard_costs import _settings


def test_scale_windows_render_in_melbourne_time_across_daylight_saving() -> None:
    """SRF-OUT-04: dashboard window labels render Melbourne 24-hour time."""
    settings = _settings()
    before = datetime(2026, 9, 24, tzinfo=UTC)
    after = datetime(2026, 10, 5, tzinfo=UTC)

    assert window_label(settings, "20:25", before) == "06:25-10:30 Melbourne"
    assert window_label(settings, "22:30", before) == "08:30-10:30 Melbourne"
    assert window_label(settings, "20:25", after) == "07:25-11:30 Melbourne"


def test_the_page_is_told_which_zone_to_render() -> None:
    """SRF-OUT-04: the page receives the Melbourne rendering zone."""
    app = build_app(InMemoryGraphStore(), FakeAzureReader(), _settings())

    page = invoke(app, "/")[2].decode("utf-8")

    assert '"timeZone": "Australia/Melbourne"' in page


def test_an_agent_the_fleet_check_refused_is_not_shown_as_simply_active() -> None:
    graph = InMemoryGraphStore()
    place_run_request(graph, run_id="fleet", tickers=("AAPL",), as_of=date(2026, 9, 23))
    for agent in ("operator", "execution"):
        graph.merge_node(
            "AgentInstance",
            agent,
            {"agent_type": agent, "state": "active", "started_at": "2026-09-23"},
        )
    checked = (datetime.now(tz=UTC) - timedelta(hours=3)).isoformat()
    graph.merge_node(
        "FleetPreflight",
        f"preflight:{checked}",
        {
            "checked_at": checked,
            "passed": False,
            "failures": [
                "unrecoverable:operator:anthropic:unrecoverable:http_400",
                "not-a-structured-failure",
            ],
        },
    )

    result = fleet_projection(graph, FakeAzureReader(), _settings(), "fleet")
    agents = {
        row["agent"]: row for row in cast("list[dict[str, Any]]", result["agents"])
    }
    stage = cast("list[dict[str, str]]", result["stages"])[2]

    assert agents["operator"]["check"] == "anthropic answered HTTP 400"
    assert "check" not in agents["execution"]
    assert stage["status"] == "warn"
    assert stage["detail"] == "2/2 active · 1 refused by the fleet check"
