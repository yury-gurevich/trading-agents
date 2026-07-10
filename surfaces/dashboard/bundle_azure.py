"""Azure log and image projections shared by the bundle and log endpoint.

Agent: surfaces
Role: attach bounded, run-window Azure evidence to the read-only dashboard.
External I/O: injected AzureReader calls only.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from surfaces.dashboard.azure_port import AzureReadError
from surfaces.dashboard.projections_infra import image_tag
from surfaces.dashboard.time_windows import latest_window, run_window

if TYPE_CHECKING:
    from datetime import datetime

    from surfaces.dashboard.azure_port import AzureReader, AzureRow
    from surfaces.dashboard.settings import DashboardSettings

_AZURE_FAILURES = (AzureReadError, KeyError, TypeError, ValueError)


def bundle_artifacts(
    azure: AzureReader | None,
    settings: DashboardSettings,
    run_day: str,
) -> tuple[dict[str, object], dict[str, object]]:
    """Return run-window per-container logs and fleet images for the bundle."""
    if azure is None or not run_day:
        return _unavailable("Log Analytics"), _unavailable("Azure image")
    try:
        start, end = run_window(run_day, settings)
        apps = azure.list_container_apps()
        jobs = azure.list_job_executions(settings.azure_job_name)
    except _AZURE_FAILURES:
        return _unavailable("Log Analytics"), _unavailable("Azure image")
    images = {str(row["name"]): _image_row(row) for row in apps}
    if jobs:
        images[settings.azure_job_name] = _image_row(jobs[0])
    rows: dict[str, list[AzureRow]] = {}
    errors: dict[str, str] = {}
    tail = min(settings.bundle_log_tail, settings.log_tail_max)
    for name in images:
        try:
            rows[name] = azure.query_logs(name, start, end, tail)
        except _AZURE_FAILURES:
            rows[name] = []
            errors[name] = "Log Analytics unavailable"
    return (
        {
            "available": not errors,
            "window": {"start": start.isoformat(), "end": end.isoformat()},
            "tail": tail,
            "containers": rows,
            "errors": errors,
        },
        {"available": True, "containers": images},
    )


def container_logs(
    azure: AzureReader | None,
    settings: DashboardSettings,
    container: str,
    tail: int,
    *,
    now: datetime | None = None,
) -> dict[str, object]:
    """Return one bounded latest-window log projection, degraded as HTTP-200 data."""
    start, end = latest_window(settings, now)
    if azure is None:
        return _log_unavailable(container, start, end, tail)
    try:
        rows = azure.query_logs(container, start, end, tail)
    except _AZURE_FAILURES:
        return _log_unavailable(container, start, end, tail)
    return {
        "available": True,
        "container": container,
        "window": {"start": start.isoformat(), "end": end.isoformat()},
        "tail": tail,
        "rows": rows,
        "message": None,
    }


def _image_row(row: AzureRow) -> dict[str, str]:
    image = str(row.get("image", ""))
    return {"image": image, "tag": image_tag(image)}


def _unavailable(source: str) -> dict[str, object]:
    return {
        "available": False,
        "message": f"{source} data unavailable",
        "containers": {},
    }


def _log_unavailable(
    container: str, start: datetime, end: datetime, tail: int
) -> dict[str, object]:
    return {
        "available": False,
        "container": container,
        "window": {"start": start.isoformat(), "end": end.isoformat()},
        "tail": tail,
        "rows": [],
        "message": "Azure data unavailable",
    }
