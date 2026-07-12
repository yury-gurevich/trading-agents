"""Dashboard Section-II projection — fleet lifecycle as logical stages.

Agent: surfaces
Role: combine graph activation/escalation proof with Azure job and replica state.
External I/O: injected GraphStore reads and AzureReader calls only.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from surfaces.dashboard.azure_port import AzureReadError
from surfaces.dashboard.projections import run_stages
from surfaces.dashboard.projections_state import run_recovery

if TYPE_CHECKING:
    from kernel import GraphStore, Node
    from surfaces.dashboard.azure_port import AzureReader, AzureRow
    from surfaces.dashboard.settings import DashboardSettings

_AZURE_FAILURES = (AzureReadError, KeyError, TypeError, ValueError)


def fleet_projection(
    graph: GraphStore,
    azure: AzureReader | None,
    settings: DashboardSettings,
    run_id: str,
) -> dict[str, object]:
    """Project run-scoped lifecycle stages and current activation state."""
    apps, jobs, azure_available = _azure_rows(azure, settings.azure_job_name)
    run_day = _run_day(graph, run_id)
    execution = _job_for_day(jobs, run_day)
    instances = _latest_instances(graph)
    recovery = run_recovery(graph, run_id)
    agents = _agent_rows(instances, recovery)
    reached = sum(bool(stage["reached"]) for stage in run_stages(graph, run_id))
    replicas = [row.get("replicas") for row in apps]
    replica_total = sum(value for value in replicas if isinstance(value, int))
    stages = [
        _stage(
            "cron",
            "Fired on schedule",
            _execution_detail(execution),
            _job_status(execution, azure_available),
        ),
        _stage(
            "master",
            "Woke first, keys ready",
            _app_detail(apps, "master"),
            _app_status(apps, "master", azure_available),
        ),
        _stage(
            "agents",
            "EHLO then tested ACTIVATE",
            f"{sum(row['state'] == 'active' for row in agents)}/{len(agents)} active",
            (
                "good"
                if agents and all(row["state"] == "active" for row in agents)
                else "warn"
            ),
        ),
        _stage(
            "control plane",
            "Served over Service Bus",
            f"{len(graph.list_nodes('CapabilityGrant'))} capability grants"
            " recorded to date",
            _control_plane_status(execution, azure_available),
        ),
        _stage(
            "pipeline",
            "Graph-pull cascade ran",
            f"{reached}/7 stages reached",
            "good" if reached == 7 else "warn",
        ),
        _stage(
            "fleet",
            "Returned to its scale window",
            f"{replica_total} replicas now",
            "good" if azure_available else "idle",
        ),
    ]
    return {
        "run_id": run_id,
        "azure_available": azure_available,
        "stages": stages,
        "agents": agents,
        "escalations": recovery["escalations"],
        "remediation_plans": recovery["remediation_plans"],
    }


def _azure_rows(
    azure: AzureReader | None, job: str
) -> tuple[list[AzureRow], list[AzureRow], bool]:
    if azure is None:
        return [], [], False
    try:
        return azure.list_container_apps(), azure.list_job_executions(job), True
    except _AZURE_FAILURES:
        return [], [], False


def _run_day(graph: GraphStore, run_id: str) -> str:
    node = graph.get_node("RunRequest", f"run-request:{run_id}")
    return str(node.props.get("requested_at", "")) if node else ""


def _job_for_day(rows: list[AzureRow], run_day: str) -> AzureRow | None:
    return next(
        (row for row in rows if str(row.get("start_time", "")).startswith(run_day)),
        rows[0] if rows else None,
    )


def _latest_instances(graph: GraphStore) -> dict[str, Node]:
    latest: dict[str, Node] = {}
    for node in graph.list_nodes("AgentInstance"):
        agent = str(node.props.get("agent_type", "unknown"))
        current = latest.get(agent)
        if current is None or str(node.props.get("started_at", "")) > str(
            current.props.get("started_at", "")
        ):
            latest[agent] = node
    return latest


def _agent_rows(
    instances: dict[str, Node], recovery: dict[str, object]
) -> list[dict[str, object]]:
    escalations = recovery["escalations"]
    assert isinstance(escalations, list)
    rows: list[dict[str, object]] = []
    for agent, node in sorted(instances.items()):
        open_escalations = [
            row
            for row in escalations
            if isinstance(row, dict)
            and row.get("agent_type") == agent
            and row.get("status") == "open"
        ]
        rows.append(
            {
                "agent": agent,
                "instance_id": node.key,
                "state": str(node.props.get("state", "unknown")),
                "started_at": str(node.props.get("started_at", "")),
                "escalation": "operator-held" if open_escalations else None,
            }
        )
    return rows


def _stage(who: str, did: str, detail: str, status: str) -> dict[str, str]:
    labels = {
        "good": "did its job",
        "warn": "needs attention",
        "crit": "failed",
        "idle": "unavailable",
    }
    return {
        "who": who,
        "did": did,
        "detail": detail,
        "status": status,
        "verdict": labels[status],
    }


def _execution_detail(row: AzureRow | None) -> str:
    if row is None:
        return "Azure job data unavailable"
    return f"{row.get('start_time', '')} - {row.get('status', 'unknown')}"


def _control_plane_status(row: AzureRow | None, available: bool) -> str:
    # idle = could not verify (no Azure, no execution row); a Failed night is a
    # real "needs attention", not an availability gap.
    if not available or row is None:
        return "idle"
    return "good" if row.get("status") == "Succeeded" else "warn"


def _job_status(row: AzureRow | None, available: bool) -> str:
    if not available or row is None:
        return "idle"
    return "good" if row.get("status") == "Succeeded" else "crit"


def _app_detail(rows: list[AzureRow], name: str) -> str:
    row = next((item for item in rows if item.get("name") == name), None)
    return str(row.get("running_status", "unavailable")) if row else "unavailable"


def _app_status(rows: list[AzureRow], name: str, available: bool) -> str:
    if not available:
        return "idle"
    row = next((item for item in rows if item.get("name") == name), None)
    return "good" if row and row.get("provisioning_state") == "Succeeded" else "crit"
