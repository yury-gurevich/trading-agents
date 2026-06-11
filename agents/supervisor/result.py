"""Supervisor response builders.

Agent: supervisor
Role: keep DispatchResult and MasterReport construction out of the agent class.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from contracts.common import Explanation, Provenance
from contracts.supervisor import DispatchResult, MasterReport

if TYPE_CHECKING:
    from agents.supervisor.domain.health import HealthFields


def rejected(run_id: str, reason: str) -> DispatchResult:
    """Build a refused dispatch result."""
    return DispatchResult(
        accepted=False,
        rejection=reason,
        provenance=Provenance(run_id=run_id, source_agent="supervisor"),
    )


def provenance(run_id: str, label: str, key: str) -> Provenance:
    """Build graph provenance for a supervisor-written node."""
    return Provenance(
        run_id=run_id,
        source_agent="supervisor",
        graph_node_id=f"{label}:{key}",
    )


def master_report(run_id: str, health: HealthFields) -> MasterReport:
    """Build the public supervisor health report."""
    return MasterReport(
        healthy=health["healthy"],
        open_incidents=health["open_incidents"],
        pending_human_flags=health["pending_human_flags"],
        last_successful_run=health["last_successful_run"],
        summary=Explanation(summary=_health_summary(health)),
        provenance=Provenance(run_id=run_id, source_agent="supervisor"),
    )


def failed_health() -> HealthFields:
    """Return a degraded health payload when graph health lookup faults."""
    return {
        "healthy": False,
        "open_incidents": 1,
        "pending_human_flags": 0,
        "last_successful_run": None,
    }


def _health_summary(health: HealthFields) -> str:
    if health["healthy"]:
        return "System health is green."
    return (
        f"{health['open_incidents']} open incidents; "
        f"{health['pending_human_flags']} pending critical flags."
    )
