"""Dashboard read-side spine and activation-bus health judgements.

Agent: surfaces
Role: keep unavailable evidence distinct from a proven failed read.
External I/O: injected GraphStore reads only.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kernel import GraphStore
    from surfaces.dashboard.azure_port import AzureRow


def spine_health(graph: GraphStore) -> dict[str, str]:
    """Return whether a graph read succeeds."""
    try:
        graph.list_nodes("RunRequest")
    except Exception:  # a backend failure is exactly the health signal
        return {"status": "unavailable", "detail": "graph read failed"}
    return {"status": "reachable", "detail": "read succeeded"}


def bus_health(
    graph: GraphStore, jobs: list[AzureRow], job_error: str | None
) -> dict[str, object]:
    """Return reachable/unreachable/unverified without treating no read as failure."""
    try:
        active = sum(
            str(node.props.get("state", "")) == "active"
            for node in graph.list_nodes("AgentInstance")
        )
    except Exception:
        return {"status": "unverified", "detail": "activation evidence unavailable"}
    detail = f"{active} active activation records"
    if job_error or not jobs:
        return {"status": "unverified", "detail": detail}
    job_status = str(jobs[0].get("status", "")).lower()
    if job_status in {"failed", "canceled", "cancelled"}:
        return {"status": "unreachable", "detail": f"failed bus-backed run; {detail}"}
    if job_status == "succeeded" and active:
        return {"status": "reachable", "detail": detail}
    return {"status": "unverified", "detail": detail}
