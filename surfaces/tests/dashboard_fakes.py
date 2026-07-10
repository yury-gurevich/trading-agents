"""Reusable fake AzureReader for dashboard projection and route tests.

Agent: surfaces
Role: provide deterministic fixture-backed Azure reads with selectable failures.
External I/O: filesystem reads of committed JSON fixtures only.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, cast

from surfaces.dashboard.azure_parsers import (
    parse_container_apps,
    parse_cost_rows,
    parse_job_executions,
    parse_log_rows,
)
from surfaces.dashboard.azure_port import AzureReadError, AzureRow

if TYPE_CHECKING:
    from datetime import datetime

_FIXTURES = Path(__file__).parent / "fixtures"


def fixture(name: str) -> dict[str, object]:
    """Load one committed Azure response fixture."""
    return cast(
        "dict[str, object]",
        json.loads((_FIXTURES / name).read_text(encoding="utf-8")),
    )


class FakeAzureReader:
    """Fixture-backed AzureReader with per-method failure switches."""

    def __init__(
        self,
        *,
        fail_apps: bool = False,
        fail_jobs: bool = False,
        fail_costs: bool = False,
        fail_logs_for: str | None = None,
    ) -> None:
        self.fail_apps = fail_apps
        self.fail_jobs = fail_jobs
        self.fail_costs = fail_costs
        self.fail_logs_for = fail_logs_for
        self.log_calls: list[tuple[str, datetime, datetime, int]] = []

    def list_container_apps(self) -> list[AzureRow]:
        """Return parsed app fixtures with deterministic current replicas."""
        if self.fail_apps:
            raise AzureReadError("apps unavailable")
        rows = parse_container_apps(fixture("azure_container_apps.json"))
        for index, row in enumerate(rows):
            row["replicas"] = index
        return rows

    def list_job_executions(self, job: str) -> list[AzureRow]:
        """Return parsed job fixtures."""
        if self.fail_jobs:
            raise AzureReadError("jobs unavailable")
        return parse_job_executions(fixture("azure_job_executions.json"))

    def query_logs(
        self, container: str, start: datetime, end: datetime, tail: int
    ) -> list[AzureRow]:
        """Record the bounded query and return parsed log fixtures."""
        self.log_calls.append((container, start, end, tail))
        if container == self.fail_logs_for:
            raise AzureReadError("logs unavailable")
        return parse_log_rows(fixture("azure_log_rows.json"))

    def query_costs(self, scope: str, month_to_date: bool) -> list[AzureRow]:
        """Return parsed cost fixtures."""
        if self.fail_costs:
            raise AzureReadError("cost unavailable")
        return parse_cost_rows(fixture("azure_cost_rows.json"))
