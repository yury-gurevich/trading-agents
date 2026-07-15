"""Dashboard deploy-currency template semantics tests.

Agent: surfaces
Role: prove dispatcher job template image drives currency judgement.
External I/O: none; Azure and GitHub reads are injected fakes.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast

import pytest

from kernel import InMemoryGraphStore
from orchestration.deploy_record import record_deploy
from surfaces.dashboard.azure_port import AzureReadError, AzureRow
from surfaces.dashboard.github_builds import MainImageBuild
from surfaces.dashboard.projections_infra import infra_projection
from surfaces.tests.test_dashboard_costs import _settings


@pytest.mark.parametrize(
    ("template_tag", "fail_template", "expected"),
    [
        ("s126", False, "current"),
        ("s125", False, "behind"),
        ("s126", True, "unverified"),
    ],
)
def test_dispatcher_template_tag_drives_deploy_currency(
    template_tag: str, fail_template: bool, expected: str
) -> None:
    graph = InMemoryGraphStore()
    record_deploy(
        graph,
        tag="s126",
        git_sha="main-sha",
        actor="operator",
        deployed_at=datetime(2026, 7, 15, tzinfo=UTC),
    )
    result = infra_projection(
        graph,
        _Azure(template_tag, execution_tag="s121", fail_template=fail_template),
        _settings(),
        github=_BuildReader(),
    )

    currency = cast("dict[str, Any]", result["deploy_currency"])
    job_summary = cast("dict[str, Any]", result["job"])
    containers = cast("list[dict[str, Any]]", result["containers"])
    assert currency["status"] == expected
    assert job_summary["last_execution_tag"] == "s121"
    job = next(row for row in containers if row["kind"] == "job")
    assert job["last_execution_tag"] == "s121"
    if expected == "current":
        assert cast("dict[str, Any]", currency["evidence"])["running_tags"] == ["s126"]


class _BuildReader:
    def latest_main_image_build(self) -> MainImageBuild:
        return MainImageBuild("main-sha", 293, "https://github.example/293")


class _Azure:
    def __init__(
        self, template_tag: str, *, execution_tag: str, fail_template: bool = False
    ) -> None:
        self.template_tag = template_tag
        self.execution_tag = execution_tag
        self.fail_template = fail_template

    def list_container_apps(self) -> list[AzureRow]:
        return [
            _app("master", "s126"),
            _app("execution", "s126"),
        ]

    def list_job_executions(self, job: str) -> list[AzureRow]:
        del job
        return [
            {
                "name": "dispatcher-cron-new",
                "status": "Succeeded",
                "start_time": "2026-07-15T22:30:00Z",
                "end_time": "2026-07-15T22:31:00Z",
                "image": f"ghcr.io/org/dispatcher:{self.execution_tag}",
            }
        ]

    def job_template_image(self, job: str) -> str:
        del job
        if self.fail_template:
            raise AzureReadError("job template unavailable")
        return f"ghcr.io/org/dispatcher:{self.template_tag}"

    def query_costs(self, scope: str, month_to_date: bool) -> list[AzureRow]:
        del scope, month_to_date
        return []

    def query_logs(
        self, container: str, start: datetime, end: datetime, tail: int
    ) -> list[AzureRow]:
        del container, start, end, tail
        return []


def _app(name: str, tag: str) -> dict[str, Any]:
    return {
        "name": name,
        "location": "Australia East",
        "image": f"ghcr.io/org/{name}:{tag}",
        "revision": f"{name}--{tag}",
        "running_status": "Running",
        "provisioning_state": "Succeeded",
        "replicas": 1,
    }
