"""Dashboard Section-I projection — live infrastructure, images, and costs.

Agent: surfaces
Role: combine Azure read-port facts with graph reachability and LLM ledger cost.
External I/O: injected GraphStore reads and AzureReader calls only.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from surfaces.dashboard.azure_port import AzureReadError
from surfaces.dashboard.llm_costs import llm_cost_projection
from surfaces.dashboard.time_windows import next_fire, window_label

if TYPE_CHECKING:
    from datetime import datetime

    from kernel import GraphStore
    from surfaces.dashboard.azure_port import AzureReader, AzureRow
    from surfaces.dashboard.settings import DashboardSettings

_AZURE_FAILURES = (AzureReadError, KeyError, TypeError, ValueError)


def infra_projection(
    graph: GraphStore,
    azure: AzureReader | None,
    settings: DashboardSettings,
    *,
    now: datetime | None = None,
) -> dict[str, object]:
    """Project the current fleet, job, hardware cost, and LLM spend."""
    apps, app_error = _apps(azure)
    jobs, job_error = _jobs(azure, settings.azure_job_name)
    hardware = _hardware(azure, _resource_scope(settings))
    containers = [_app_row(row, jobs) for row in apps]
    if jobs:
        containers.append(_job_row(settings.azure_job_name, jobs[0]))
    location = str(apps[0].get("location", "")) if apps else None
    spine = _spine_health(graph)
    bus = _bus_health(graph, jobs)
    return {
        "available": app_error is None,
        "message": app_error,
        "environment": {
            "name": settings.azure_environment_name,
            "location": location,
            "app_count": len(apps) if app_error is None else None,
            "status": "available" if app_error is None else "unavailable",
        },
        "spine": spine,
        "bus": bus,
        "job": _job_summary(settings, jobs, job_error, now),
        "scale_windows": {
            "master": window_label(settings),
            "agents": (
                f"{settings.agent_window_start_utc}-{settings.window_end_utc} UTC"
            ),
        },
        "containers": containers,
        "hardware_cost": hardware,
        "llm_cost": llm_cost_projection(graph, now=now),
    }


def image_tag(image: str) -> str:
    """Return a compact tag or digest without judging fleet currency."""
    if "@" in image:
        return image.rsplit("@", 1)[1][:19]
    last = image.rsplit("/", 1)[-1]
    return last.rsplit(":", 1)[1] if ":" in last else "untagged"


def _apps(azure: AzureReader | None) -> tuple[list[AzureRow], str | None]:
    if azure is None:
        return [], "Azure data unavailable"
    try:
        return azure.list_container_apps(), None
    except AzureReadError as exc:
        return [], exc.public_message
    except _AZURE_FAILURES:
        return [], "Azure data unavailable"


def _jobs(azure: AzureReader | None, name: str) -> tuple[list[AzureRow], str | None]:
    if azure is None:
        return [], "Azure data unavailable"
    try:
        return azure.list_job_executions(name), None
    except AzureReadError as exc:
        return [], exc.public_message
    except _AZURE_FAILURES:
        return [], "Azure job data unavailable"


def _hardware(azure: AzureReader | None, scope: str) -> dict[str, object]:
    if azure is None:
        return {
            "available": False,
            "message": "Azure data unavailable",
            "total": None,
            "services": [],
        }
    try:
        rows = azure.query_costs(scope, True)
    except _AZURE_FAILURES:
        return {
            "available": False,
            "message": "Cost Management unavailable (permission or transport)",
            "total": None,
            "services": [],
        }
    services = sorted(
        rows, key=lambda row: float(cast("float", row["cost"])), reverse=True
    )
    return {
        "available": True,
        "message": None,
        "currency": str(services[0]["currency"]) if services else "USD",
        "total": round(sum(float(cast("float", row["cost"])) for row in services), 6),
        "services": services,
    }


def _app_row(row: AzureRow, jobs: list[AzureRow]) -> dict[str, object]:
    image = str(row["image"])
    return {
        **row,
        "kind": "app",
        "image_tag": image_tag(image),
        "last_window": str(jobs[0]["start_time"]) if jobs else None,
        "state": (
            "healthy" if row["provisioning_state"] == "Succeeded" else "degraded"
        ),
    }


def _job_row(name: str, row: AzureRow) -> dict[str, object]:
    image = str(row["image"])
    return {
        "name": name,
        "kind": "job",
        "image": image,
        "image_tag": image_tag(image),
        "replicas": None,
        "last_window": row["start_time"],
        "state": str(row["status"]).lower(),
    }


def _job_summary(
    settings: DashboardSettings,
    rows: list[AzureRow],
    error: str | None,
    now: datetime | None,
) -> dict[str, object]:
    latest = rows[0] if rows else {}
    return {
        "name": settings.azure_job_name,
        "status": latest.get("status", "unavailable"),
        "last_start": latest.get("start_time"),
        "last_end": latest.get("end_time"),
        "message": error,
        "next_fire": next_fire(settings, now),
    }


def _spine_health(graph: GraphStore) -> dict[str, str]:
    try:
        graph.list_nodes("RunRequest")
    except Exception:  # a backend failure is exactly the health signal
        return {"status": "unavailable", "detail": "graph read failed"}
    return {"status": "reachable", "detail": "read succeeded"}


def _bus_health(graph: GraphStore, jobs: list[AzureRow]) -> dict[str, object]:
    active = sum(
        str(node.props.get("state", "")) == "active"
        for node in graph.list_nodes("AgentInstance")
    )
    succeeded = bool(jobs) and jobs[0].get("status") == "Succeeded"
    status = "reachable" if active and succeeded else "unavailable"
    return {"status": status, "detail": f"{active} active activation records"}


def _resource_scope(settings: DashboardSettings) -> str:
    return (
        f"/subscriptions/{settings.azure_subscription_id}"
        f"/resourceGroups/{settings.azure_resource_group}"
    )
