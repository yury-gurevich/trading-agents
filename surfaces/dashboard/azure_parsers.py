"""Pure parsers for Azure REST payloads used by the operations dashboard.

Agent: surfaces
Role: turn fixture-shaped ARM, Logs, and Cost payloads into stable read rows.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from surfaces.dashboard.azure_port import AzureRow


def parse_container_apps(payload: dict[str, object]) -> list[AzureRow]:
    """Parse the ARM Container Apps collection without performing I/O."""
    result: list[AzureRow] = []
    for item in cast("list[dict[str, Any]]", payload["value"]):
        props = cast("dict[str, Any]", item["properties"])
        template = cast("dict[str, Any]", props["template"])
        containers = cast("list[dict[str, Any]]", template["containers"])
        image = str(containers[0].get("image", "")) if containers else ""
        result.append(
            {
                "name": str(item["name"]),
                "location": str(item.get("location", "")),
                "image": image,
                "revision": str(props.get("latestRevisionName", "")),
                "running_status": str(props.get("runningStatus", "unknown")),
                "provisioning_state": str(props.get("provisioningState", "unknown")),
                "replicas": None,
            }
        )
    return result


def parse_replica_count(payload: dict[str, object]) -> int:
    """Count current replicas in an ARM revision-replica collection."""
    return len(cast("list[object]", payload["value"]))


def parse_job_executions(payload: dict[str, object]) -> list[AzureRow]:
    """Parse Container Apps job execution history, newest first."""
    rows: list[AzureRow] = []
    for item in cast("list[dict[str, Any]]", payload["value"]):
        props = cast("dict[str, Any]", item["properties"])
        template = cast("dict[str, Any]", props.get("template", {}))
        containers = cast("list[dict[str, Any]]", template.get("containers", []))
        image = str(containers[0].get("image", "")) if containers else ""
        rows.append(
            {
                "name": str(item["name"]),
                "status": str(props.get("status", "unknown")),
                "start_time": str(props.get("startTime", "")),
                "end_time": str(props.get("endTime", "")),
                "image": image,
            }
        )
    rows.sort(key=lambda row: str(row["start_time"]), reverse=True)
    return rows


def parse_log_rows(payload: dict[str, object]) -> list[AzureRow]:
    """Parse the first Logs query table using its declared column names."""
    tables = cast("list[dict[str, Any]]", payload["tables"])
    if not tables:
        return []
    table = tables[0]
    names = [str(column["name"]) for column in table["columns"]]
    result: list[AzureRow] = []
    for raw in cast("list[list[object]]", table["rows"]):
        row = dict(zip(names, raw, strict=False))
        message = str(row.get("message", ""))
        result.append(
            {
                "timestamp": str(row.get("timestamp", "")),
                "level": _log_level(message),
                "message": message,
                "stream": str(row.get("stream", "")),
                "container": str(row.get("container", "")),
                "revision": str(row.get("revision", "")),
            }
        )
    return result


def parse_cost_rows(payload: dict[str, object]) -> list[AzureRow]:
    """Parse Cost Management rows by column name, not positional assumptions."""
    props = cast("dict[str, Any]", payload["properties"])
    names = [str(column["name"]) for column in props["columns"]]
    rows: list[AzureRow] = []
    for raw in cast("list[list[object]]", props["rows"]):
        row = dict(zip(names, raw, strict=False))
        rows.append(
            {
                "service": str(row.get("ServiceName", "Unassigned")),
                "cost": float(cast("float | int | str", row.get("PreTaxCost", 0.0))),
                "currency": str(row.get("Currency", "USD")),
            }
        )
    return rows


def _log_level(message: str) -> str:
    lowered = message.lower()
    if any(marker in lowered for marker in ("error", "exception", "flag raised")):
        return "error"
    if any(marker in lowered for marker in ("warn", "divergence", "degraded")):
        return "warning"
    return "info"
