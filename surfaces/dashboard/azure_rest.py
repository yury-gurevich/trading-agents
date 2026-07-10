"""Plain-REST AzureReader implementation with injectable authenticated sends.

Agent: surfaces
Role: read Container Apps, Logs, and Cost Management through Azure REST APIs.
External I/O: HTTPS GET/POST through an injected sender; Azure Identity token reads.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING
from urllib.parse import quote, urlencode

from surfaces.dashboard.azure_http import AzureIdentitySend
from surfaces.dashboard.azure_parsers import (
    parse_container_apps,
    parse_cost_rows,
    parse_job_executions,
    parse_log_rows,
    parse_replica_count,
)
from surfaces.dashboard.azure_port import AzureReadError

if TYPE_CHECKING:
    from collections.abc import Callable
    from datetime import datetime

    from surfaces.dashboard.azure_http import JsonSend
    from surfaces.dashboard.azure_port import AzureRow
    from surfaces.dashboard.settings import DashboardSettings

_ARM = "https://management.azure.com"
_ARM_SCOPE = f"{_ARM}/.default"
_LOGS = "https://api.loganalytics.io/v1/workspaces"
_LOGS_SCOPE = "https://api.loganalytics.io/.default"
_APP_API = "2024-03-01"
_COST_API = "2025-03-01"


class AzureRestReader:
    """AzureReader backed by ARM, Logs Query, and Cost Management REST."""

    def __init__(
        self,
        settings: DashboardSettings,
        *,
        send: JsonSend,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        """Bind dashboard settings, the injected sender, and cache clock."""
        self._settings = settings
        self._send = send
        self._clock = clock
        self._apps_cache: tuple[float, list[AzureRow]] | None = None
        self._jobs_cache: dict[str, tuple[float, list[AzureRow]]] = {}
        self._cost_cache: dict[str, tuple[float, list[AzureRow]]] = {}

    def list_container_apps(self) -> list[AzureRow]:
        """List apps and add current replica counts from their latest revisions."""
        cached = self._cached(self._apps_cache, self._settings.fleet_cache_ttl_seconds)
        if cached is not None:
            return cached
        query = urlencode({"api-version": _APP_API})
        url = f"{self._resource_root()}/containerApps?{query}"
        rows = parse_container_apps(self._send("GET", url, _ARM_SCOPE, None))
        for row in rows:
            revision = str(row["revision"])
            if not revision:
                continue
            path = "/containerApps/{}/revisions/{}/replicas".format(
                quote(str(row["name"]), safe=""), quote(revision, safe="")
            )
            try:
                payload = self._send(
                    "GET",
                    f"{self._resource_root()}{path}?api-version={_APP_API}",
                    _ARM_SCOPE,
                    None,
                )
                row["replicas"] = parse_replica_count(payload)
            except AzureReadError:
                row["replicas"] = None
        self._apps_cache = (self._clock(), rows)
        return [dict(row) for row in rows]

    def list_job_executions(self, job: str) -> list[AzureRow]:
        """List recent executions for one scheduled Container Apps job."""
        cached = self._cached(
            self._jobs_cache.get(job), self._settings.fleet_cache_ttl_seconds
        )
        if cached is not None:
            return cached
        url = (
            f"{self._resource_root()}/jobs/{quote(job, safe='')}/executions"
            f"?api-version={_APP_API}"
        )
        rows = parse_job_executions(self._send("GET", url, _ARM_SCOPE, None))
        self._jobs_cache[job] = (self._clock(), rows)
        return [dict(row) for row in rows]

    def query_logs(
        self, container: str, start: datetime, end: datetime, tail: int
    ) -> list[AzureRow]:
        """Query a bounded, chronological Container Apps console-log excerpt."""
        escaped = container.replace("'", "''")
        query = (
            "ContainerAppConsoleLogs_CL\n"
            f"| where ContainerAppName_s == '{escaped}'\n"
            "| project timestamp=TimeGenerated, message=Log_s, stream=Stream_s, "
            "container=ContainerName_s, revision=RevisionName_s\n"
            "| order by timestamp desc\n"
            f"| take {tail}\n| order by timestamp asc"
        )
        url = f"{_LOGS}/{quote(self._settings.azure_workspace_id, safe='')}/query"
        body = {"query": query, "timespan": f"{start.isoformat()}/{end.isoformat()}"}
        return parse_log_rows(self._send("POST", url, _LOGS_SCOPE, body))

    def query_costs(self, scope: str, month_to_date: bool) -> list[AzureRow]:
        """Query and cache month-to-date pretax cost grouped by Azure service."""
        if not month_to_date:
            raise ValueError("only month-to-date cost queries are supported")
        cached = self._cached(
            self._cost_cache.get(scope), self._settings.cost_cache_ttl_seconds
        )
        if cached is not None:
            return cached
        body: dict[str, object] = {
            "type": "Usage",
            "timeframe": "MonthToDate",
            "dataset": {
                "granularity": "None",
                "aggregation": {"totalCost": {"name": "PreTaxCost", "function": "Sum"}},
                "grouping": [{"type": "Dimension", "name": "ServiceName"}],
            },
        }
        url = (
            f"{_ARM}{scope}/providers/Microsoft.CostManagement/query"
            f"?api-version={_COST_API}"
        )
        rows = parse_cost_rows(self._send("POST", url, _ARM_SCOPE, body))
        self._cost_cache[scope] = (self._clock(), rows)
        return [dict(row) for row in rows]

    def _resource_root(self) -> str:
        sub = quote(self._settings.azure_subscription_id, safe="")
        group = quote(self._settings.azure_resource_group, safe="")
        return (
            f"{_ARM}/subscriptions/{sub}/resourceGroups/{group}/providers/Microsoft.App"
        )

    def _cached(
        self, entry: tuple[float, list[AzureRow]] | None, ttl: float
    ) -> list[AzureRow] | None:
        if entry is None or self._clock() - entry[0] >= ttl:
            return None
        return [dict(row) for row in entry[1]]


def build_azure_reader(settings: DashboardSettings) -> AzureRestReader | None:
    """Build the live reader only when every required Azure coordinate exists."""
    if not settings.azure_subscription_id or not settings.azure_workspace_id:
        return None
    try:
        sender = AzureIdentitySend(
            timeout=settings.azure_timeout_seconds,
            credential_mode=settings.azure_credential_mode,
        )
    except (ImportError, AzureReadError):
        return None
    return AzureRestReader(settings, send=sender)
