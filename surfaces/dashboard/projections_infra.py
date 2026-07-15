"""Dashboard Section-I projection — live infrastructure, images, and costs.

Agent: surfaces
Role: combine injected read facts into an honest infrastructure projection.
External I/O: injected GraphStore, AzureReader, and GitHubReader reads only.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from surfaces.dashboard.llm_costs import llm_cost_projection
from surfaces.dashboard.projections_azure import (
    app_row,
    apps,
    hardware,
    image_tag,
    job_row,
    job_template_image,
    jobs,
)
from surfaces.dashboard.projections_currency import deploy_currency_projection
from surfaces.dashboard.projections_health import bus_health, spine_health
from surfaces.dashboard.time_windows import next_fire, window_label

if TYPE_CHECKING:
    from datetime import datetime

    from kernel import GraphStore
    from surfaces.dashboard.azure_port import AzureReader, AzureRow
    from surfaces.dashboard.github_builds import GitHubReader
    from surfaces.dashboard.settings import DashboardSettings

__all__ = ["image_tag", "infra_projection"]


def infra_projection(
    graph: GraphStore,
    azure: AzureReader | None,
    settings: DashboardSettings,
    *,
    now: datetime | None = None,
    github: GitHubReader | None = None,
) -> dict[str, object]:
    """Project the fleet, job, reachability, deploy currency, and costs."""
    app_rows, app_error = apps(azure)
    job_rows, job_error = jobs(azure, settings.azure_job_name)
    template_image, template_error = job_template_image(azure, settings.azure_job_name)
    containers: list[dict[str, Any]] = [app_row(row, job_rows) for row in app_rows]
    if job_rows:
        containers.append(job_row(settings.azure_job_name, job_rows[0], template_image))
    location = str(app_rows[0].get("location", "")) if app_rows else None
    currency = deploy_currency_projection(
        graph,
        containers,
        github,
        azure_verified=(
            app_error is None
            and job_error is None
            and template_error is None
            and bool(job_rows)
        ),
    )
    return {
        "available": app_error is None,
        "message": app_error,
        "environment": {
            "name": settings.azure_environment_name,
            "location": location,
            "app_count": len(app_rows) if app_error is None else None,
            "status": "available" if app_error is None else "unavailable",
        },
        "spine": spine_health(graph),
        "bus": bus_health(graph, job_rows, job_error),
        "deploy_currency": currency,
        "job": _job_summary(
            settings, job_rows, job_error or template_error, template_image, now
        ),
        "scale_windows": {
            "master": window_label(settings),
            "agents": (
                f"{settings.agent_window_start_utc}-{settings.window_end_utc} UTC"
            ),
        },
        "containers": containers,
        "hardware_cost": hardware(azure, _resource_scope(settings)),
        "llm_cost": llm_cost_projection(graph, now=now),
    }


def _job_summary(
    settings: DashboardSettings,
    rows: list[AzureRow],
    error: str | None,
    template_image: str | None,
    now: datetime | None,
) -> dict[str, object]:
    latest = rows[0] if rows else {}
    return {
        "name": settings.azure_job_name,
        "status": latest.get("status", "unavailable"),
        "last_start": latest.get("start_time"),
        "last_end": latest.get("end_time"),
        "template_tag": image_tag(template_image or "") if template_image else None,
        "last_execution_tag": (
            image_tag(str(latest["image"])) if latest.get("image") else None
        ),
        "message": error,
        "next_fire": next_fire(settings, now),
    }


def _resource_scope(settings: DashboardSettings) -> str:
    return (
        f"/subscriptions/{settings.azure_subscription_id}"
        f"/resourceGroups/{settings.azure_resource_group}"
    )


_spine_health = spine_health
