"""Azure read adapters used by the infrastructure projection.

Agent: surfaces
Role: normalize optional Azure reads into stable read-model rows.
External I/O: injected AzureReader calls only.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from surfaces.dashboard.azure_port import AzureReadError

if TYPE_CHECKING:
    from surfaces.dashboard.azure_port import AzureReader, AzureRow

_FAILURES = (AzureReadError, KeyError, TypeError, ValueError)


def image_tag(image: str) -> str:
    """Return a compact tag or digest without judging fleet currency."""
    if "@" in image:
        return image.rsplit("@", 1)[1][:19]
    last = image.rsplit("/", 1)[-1]
    return last.rsplit(":", 1)[1] if ":" in last else "untagged"


def apps(azure: AzureReader | None) -> tuple[list[AzureRow], str | None]:
    """Read Container Apps or return a sanitized unavailable message."""
    if azure is None:
        return [], "Azure data unavailable"
    try:
        return azure.list_container_apps(), None
    except AzureReadError as exc:
        return [], exc.public_message
    except _FAILURES:
        return [], "Azure data unavailable"


def jobs(azure: AzureReader | None, name: str) -> tuple[list[AzureRow], str | None]:
    """Read job executions or return a sanitized unavailable message."""
    if azure is None:
        return [], "Azure data unavailable"
    try:
        return azure.list_job_executions(name), None
    except AzureReadError as exc:
        return [], exc.public_message
    except _FAILURES:
        return [], "Azure job data unavailable"


def job_template_image(
    azure: AzureReader | None, name: str
) -> tuple[str | None, str | None]:
    """Read the dispatcher's configured image or return a sanitized error."""
    if azure is None:
        return None, "Azure job template unavailable"
    try:
        return azure.job_template_image(name), None
    except AzureReadError as exc:
        return None, exc.public_message
    except _FAILURES:
        return None, "Azure job template unavailable"


def hardware(azure: AzureReader | None, scope: str) -> dict[str, object]:
    """Read month-to-date Azure costs."""
    if azure is None:
        return _missing("Azure data unavailable")
    try:
        rows = azure.query_costs(scope, True)
    except _FAILURES:
        return _missing("Cost Management unavailable (permission or transport)")
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


def app_row(row: AzureRow, job_rows: list[AzureRow]) -> dict[str, object]:
    """Normalize one app row."""
    image = str(row["image"])
    return {
        **row,
        "kind": "app",
        "image_tag": image_tag(image),
        "last_window": str(job_rows[0]["start_time"]) if job_rows else None,
        "state": "healthy" if row["provisioning_state"] == "Succeeded" else "degraded",
    }


def job_row(name: str, row: AzureRow, template_image: str | None) -> dict[str, object]:
    """Normalize the dispatcher job row."""
    execution_image = str(row["image"])
    template_tag = image_tag(template_image or "")
    return {
        "name": name,
        "kind": "job",
        "image": template_image or "",
        "image_tag": template_tag if template_image else "unverified",
        "last_execution_image": execution_image,
        "last_execution_tag": image_tag(execution_image),
        "replicas": None,
        "last_window": row["start_time"],
        "state": str(row["status"]).lower(),
    }


def _missing(message: str) -> dict[str, object]:
    return {"available": False, "message": message, "total": None, "services": []}
