"""Dashboard fleet lifecycle projection tests.

Agent: surfaces
Role: prove graph-first activation/escalation state plus Azure lifecycle stages.
External I/O: none; graph is in-memory and AzureReader is fake.
"""

from __future__ import annotations

from datetime import date
from typing import Any, cast

from kernel import InMemoryGraphStore
from orchestration.start import place_run_request
from surfaces.dashboard.projections_fleet import fleet_projection
from surfaces.tests.dashboard_fakes import FakeAzureReader
from surfaces.tests.test_dashboard_costs import _settings


def _graph() -> InMemoryGraphStore:
    graph = InMemoryGraphStore()
    place_run_request(graph, run_id="fleet", tickers=("AAPL",), as_of=date(2026, 7, 9))
    graph.merge_node(
        "AgentInstance",
        "old",
        {"agent_type": "execution", "state": "refused", "started_at": "2026-07-08"},
    )
    graph.merge_node(
        "AgentInstance",
        "new",
        {"agent_type": "execution", "state": "active", "started_at": "2026-07-09"},
    )
    graph.merge_node(
        "AgentInstance",
        "provider",
        {"agent_type": "provider", "state": "active", "started_at": "2026-07-09"},
    )
    graph.merge_node(
        "AgentInstance",
        "stale",
        {"agent_type": "execution", "state": "refused", "started_at": "2026-07-01"},
    )
    graph.merge_node("CapabilityGrant", "grant", {"capability": "serve"})
    graph.merge_node(
        "Escalation",
        "open",
        {
            "agent_type": "provider",
            "status": "open",
            "created_at": "2026-07-09T22:30:00Z",
        },
    )
    return graph


def test_fleet_projects_latest_activation_and_recovery_ladder() -> None:
    result = fleet_projection(_graph(), FakeAzureReader(), _settings(), "fleet")
    agents = {
        row["agent"]: row for row in cast("list[dict[str, Any]]", result["agents"])
    }
    stages = cast("list[dict[str, str]]", result["stages"])
    assert result["azure_available"] is True
    assert agents["execution"]["instance_id"] == "new"
    assert agents["provider"]["escalation"] == "operator-held"
    assert stages[0]["status"] == "good"
    assert stages[1]["status"] == "good"
    assert stages[3]["status"] == "good"
    assert str(stages[3]["detail"]).endswith("recorded to date")
    assert stages[4]["status"] == "warn"


def test_fleet_degrades_without_azure_and_handles_empty_graph() -> None:
    graph = InMemoryGraphStore()
    result = fleet_projection(graph, None, _settings(), "missing")
    stages = cast("list[dict[str, str]]", result["stages"])
    assert result["azure_available"] is False
    assert stages[0]["status"] == "idle"
    assert stages[1]["detail"] == "unavailable"
    assert stages[2]["status"] == "warn"
    assert stages[3]["status"] == "idle"
    failed = fleet_projection(
        graph, FakeAzureReader(fail_apps=True), _settings(), "missing"
    )
    assert failed["azure_available"] is False


class FailedJobReader(FakeAzureReader):
    def list_job_executions(self, job: str) -> list[dict[str, object]]:
        rows = super().list_job_executions(job)
        rows[0]["status"] = "Failed"
        rows[0]["start_time"] = "2026-07-01T22:30:00Z"
        return rows


def test_fleet_failed_latest_job_is_critical_fallback() -> None:
    result = fleet_projection(_graph(), FailedJobReader(), _settings(), "fleet")
    stages = cast("list[dict[str, str]]", result["stages"])
    assert stages[0]["status"] == "crit"
    assert stages[3]["status"] == "warn"


class EmptyJobsReader(FakeAzureReader):
    def list_job_executions(self, job: str) -> list[dict[str, object]]:
        return []


def test_fleet_no_execution_rows_reads_could_not_verify() -> None:
    """A reachable Azure with no execution rows is unverified, not failed."""
    result = fleet_projection(_graph(), EmptyJobsReader(), _settings(), "fleet")
    stages = cast("list[dict[str, str]]", result["stages"])
    assert result["azure_available"] is True
    assert stages[0]["status"] == "idle"
    assert stages[3]["status"] == "idle"
