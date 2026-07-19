"""Dashboard LLM and hardware cost projection tests.

Agent: surfaces
Role: prove catalogue pricing, unknown-model honesty, and Azure cost degradation.
External I/O: committed pricing JSON only; graph and Azure reads are fakes.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast

from kernel import InMemoryGraphStore
from surfaces.dashboard.llm_costs import llm_cost_projection
from surfaces.dashboard.projections_health import bus_health
from surfaces.dashboard.projections_infra import (
    _spine_health,
    image_tag,
    infra_projection,
)
from surfaces.dashboard.settings import DashboardSettings
from surfaces.tests.dashboard_fakes import FakeAzureReader

NOW = datetime(2026, 7, 10, 12, tzinfo=UTC)


def _settings() -> DashboardSettings:
    return DashboardSettings.model_construct(
        azure_subscription_id="sub",
        azure_resource_group="rg",
        azure_workspace_id="ws",
        azure_environment_name="trading-agents-env",
        azure_job_name="dispatcher-cron",
        azure_timeout_seconds=20.0,
        azure_credential_mode="auto",
        fleet_cache_ttl_seconds=30.0,
        cost_cache_ttl_seconds=300.0,
        projection_cache_ttl_seconds=5.0,
        self_heal_refetch_seconds=90.0,
        github_repository="yury-gurevich/trading-agents",
        github_image_workflow="build-images.yml",
        github_timeout_seconds=10.0,
        log_tail_default=200,
        log_tail_max=500,
        bundle_log_tail=40,
        master_window_start_utc="22:25",
        agent_window_start_utc="22:30",
        window_end_utc="00:30",
        dispatcher_fire_utc="22:30",
    )


def _llm_node(
    graph: InMemoryGraphStore,
    key: str,
    model: str,
    tokens_in: int,
    tokens_out: int,
    created_at: str = "2026-07-10T01:00:00+00:00",
) -> None:
    graph.merge_node(
        "LLMCall",
        key,
        {
            "model": model,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "created_at": created_at,
        },
    )


def test_pricing_known_tokens_and_unknown_model_is_untracked() -> None:
    graph = InMemoryGraphStore()
    _llm_node(graph, "known", "gpt-5.5", 1_000_000, 1_000_000)
    _llm_node(graph, "unknown", "future-model", 7, 9)
    _llm_node(
        graph,
        "old",
        "gpt-5.5",
        1_000_000,
        1_000_000,
        "2026-06-30T23:59:00+00:00",
    )
    result = llm_cost_projection(graph, now=NOW)
    rows = {row["model"]: row for row in cast("list[dict[str, Any]]", result["models"])}
    assert rows["gpt-5.5"]["source_cost"] == 35.0
    assert rows["gpt-5.5"]["cost"] == 48.807698
    assert rows["future-model"]["status"] == "untracked"
    assert rows["future-model"]["cost"] is None
    assert result["total"] == 48.807698
    assert result["currency"] == "AUD"
    assert cast("dict[str, Any]", result["fx"])["bank"] == (
        "Commonwealth Bank of Australia"
    )
    assert result["untracked_models"] == 1
    assert "deliberation" in str(result["coverage_note"])


def test_infra_projects_service_costs_and_images() -> None:
    graph = InMemoryGraphStore()
    graph.merge_node("AgentInstance", "i", {"state": "active"})
    result = infra_projection(graph, FakeAzureReader(), _settings(), now=NOW)
    hardware = cast("dict[str, Any]", result["hardware_cost"])
    assert result["available"] is True
    assert cast("dict[str, Any]", result["environment"])["app_count"] == 3
    assert hardware["total"] == 7.29
    assert hardware["services"][0]["service"] == "Service Bus"
    assert len(cast("list[object]", result["containers"])) == 4
    assert cast("dict[str, Any]", result["bus"])["status"] == "reachable"
    assert cast("dict[str, Any]", result["deploy_currency"])["status"] == ("unverified")


def test_infra_degraded_and_cost_permission_finding() -> None:
    graph = InMemoryGraphStore()
    degraded = infra_projection(graph, None, _settings(), now=NOW)
    assert degraded["available"] is False
    assert degraded["message"] == "Azure data unavailable"
    assert cast("dict[str, Any]", degraded["hardware_cost"])["total"] is None
    partial = infra_projection(
        graph, FakeAzureReader(fail_costs=True, fail_jobs=True), _settings(), now=NOW
    )
    cost = cast("dict[str, Any]", partial["hardware_cost"])
    assert cost["available"] is False
    assert "permission" in str(cost["message"])
    assert cast("dict[str, Any]", partial["job"])["status"] == "unavailable"
    assert cast("dict[str, Any]", partial["job"])["message"] == "jobs unavailable"
    apps_failed = infra_projection(
        graph, FakeAzureReader(fail_apps=True), _settings(), now=NOW
    )
    assert apps_failed["available"] is False
    assert apps_failed["message"] == "apps unavailable"


def test_infra_generic_reader_failure_keeps_generic_message() -> None:
    class BrokenReader(FakeAzureReader):
        def list_container_apps(self) -> list[dict[str, object]]:
            raise ValueError("unparseable")

        def list_job_executions(self, job: str) -> list[dict[str, object]]:
            raise ValueError("unparseable")

    result = infra_projection(
        InMemoryGraphStore(), BrokenReader(), _settings(), now=NOW
    )
    job = cast("dict[str, Any]", result["job"])
    assert result["message"] == "Azure data unavailable"
    assert job["message"] == "Azure job data unavailable"


def test_spine_health_reports_graph_read_failure() -> None:
    class BrokenGraph:
        def list_nodes(self, label: str) -> tuple[object, ...]:
            raise RuntimeError("offline")

    assert _spine_health(cast("Any", BrokenGraph()))["status"] == "unavailable"


def test_bus_unavailable_read_is_unverified_and_failed_read_is_unreachable() -> None:
    graph = InMemoryGraphStore()
    graph.merge_node("AgentInstance", "i", {"state": "active"})
    unavailable = infra_projection(graph, None, _settings(), now=NOW)

    class FailedJobReader(FakeAzureReader):
        def list_job_executions(self, job: str) -> list[dict[str, object]]:
            rows = super().list_job_executions(job)
            rows[0]["status"] = "Failed"
            return rows

    failed = infra_projection(graph, FailedJobReader(), _settings(), now=NOW)
    assert cast("dict[str, Any]", unavailable["bus"])["status"] == "unverified"
    assert cast("dict[str, Any]", failed["bus"])["status"] == "unreachable"


def test_bus_graph_failure_is_unverified() -> None:
    class BrokenGraph:
        def list_nodes(self, label: str) -> tuple[object, ...]:
            raise RuntimeError("offline")

    assert bus_health(cast("Any", BrokenGraph()), [], None) == {
        "status": "unverified",
        "detail": "activation evidence unavailable",
    }


def test_image_tag_handles_tag_digest_and_missing_tag() -> None:
    assert image_tag("ghcr.io/org/app:s123") == "s123"
    assert image_tag("ghcr.io/org/app@sha256:1234567890abcdef") == "sha256:1234567890ab"
    assert image_tag("ghcr.io/org/app") == "untagged"
