"""Dashboard master-verdict projection over existing read-side facts.

Agent: surfaces
Role: combine acceptance, pipeline stages, vitals, and recovery evidence into one
      binary light and deterministic operator summary. No telemetry and no writes.
External I/O: injected GraphStore reads and optional injected AzureReader calls.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING

from surfaces.dashboard.projections import run_stages, run_verdict
from surfaces.dashboard.projections_state import run_recovery
from surfaces.dashboard.projections_summary import (
    _as_int,
    _missing_stage,
    _nested_value,
    _summary,
)
from surfaces.dashboard.projections_vitals import vitals_projection

if TYPE_CHECKING:
    from datetime import datetime

    from kernel import GraphStore
    from surfaces.dashboard.azure_port import AzureReader
    from surfaces.dashboard.github_builds import GitHubReader
    from surfaces.dashboard.settings import DashboardSettings


def verdict_projection(
    graph: GraphStore,
    run_id: str,
    azure: AzureReader | None,
    settings: DashboardSettings,
    *,
    now: datetime | None = None,
    github: GitHubReader | None = None,
) -> dict[str, object]:
    """Read existing evidence and project the selected run's master verdict."""
    acceptance = run_verdict(graph, run_id)
    stages = run_stages(graph, run_id)
    vitals = vitals_projection(graph, azure, settings, run_id, now=now, github=github)
    recovery = run_recovery(graph, run_id)
    return project_verdict(acceptance, stages, vitals, recovery)


def project_verdict(
    acceptance: Mapping[str, object],
    stages: list[dict[str, object]],
    vitals: Mapping[str, object],
    recovery: Mapping[str, object],
) -> dict[str, object]:
    """Pure binary-light truth table over already projected facts."""
    verdict = str(acceptance.get("verdict", "FAIL"))
    faults = _faults(verdict, stages, vitals, recovery)
    warnings = _warnings(acceptance, vitals)
    # UNPROVEN is not a fault: orders queued for the open are normal, and a nightly
    # false RED would train the operator to ignore the light. It is never silent
    # either — it carries a warning and says UNPROVEN in the summary (DL-59).
    light = (
        "GREEN" if verdict in {"PASS", "NO_TRADE", "UNPROVEN"} and not faults else "RED"
    )
    projected = dict(acceptance)
    projected.update(
        {
            "light": light,
            "summary": _summary(
                verdict, stages, faults, confidence_bar=acceptance.get("confidence_bar")
            ),
            "next_fire": _nested_value(vitals, "next_fire", "unavailable"),
            "warning_count": len(warnings),
            "warnings": warnings,
            "faults": faults,
        }
    )
    return projected


def _faults(
    verdict: str,
    stages: list[dict[str, object]],
    vitals: Mapping[str, object],
    recovery: Mapping[str, object],
) -> list[dict[str, str]]:
    faults: list[dict[str, str]] = []
    if verdict == "FAIL":
        faults.append({"code": "acceptance", "message": "Acceptance failed"})
    if _nested_value(vitals, "spine", "unavailable", key="status") != "reachable":
        faults.append({"code": "spine", "message": "Graph spine is unreachable"})
    if _nested_value(vitals, "bus", "unverified", key="status") == "unreachable":
        faults.append({"code": "bus", "message": "Activation bus is unreachable"})
    escalations = recovery.get("escalations", [])
    if isinstance(escalations, list) and any(
        isinstance(row, Mapping) and row.get("status") == "open" for row in escalations
    ):
        faults.append(
            {"code": "operator_held", "message": "An escalation needs the operator"}
        )
    missing = _missing_stage(stages)
    if missing is not None:
        faults.append({"code": "stalled", "message": f"Run stalled before {missing}"})
    return faults


def _warnings(
    acceptance: Mapping[str, object], vitals: Mapping[str, object]
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    pending = _as_int(vitals.get("pending_flags"))
    degraded = _as_int(_nested_value(vitals, "degraded_feeds", 0, key="count"))
    untracked = _nested_value(vitals, "mtd_cost", [], key="untracked_llm_models")
    bus = _nested_value(vitals, "bus", "unverified", key="status")
    currency = _nested_value(vitals, "deploy_currency", "unverified", key="status")
    if pending:
        rows.append({"code": "pending_flags", "message": f"{pending} pending flags"})
    if degraded:
        rows.append({"code": "degraded_feeds", "message": f"{degraded} degraded feeds"})
    if isinstance(untracked, list) and untracked:
        rows.append(
            {"code": "untracked_spend", "message": "Some model spend is untracked"}
        )
    if bus == "unverified":
        rows.append(
            {"code": "bus_unverified", "message": "Activation bus is unverified"}
        )
    if currency == "behind":
        rows.append(
            {"code": "deploy_behind", "message": "Fleet deploy currency is behind"}
        )
    elif currency == "unverified":
        rows.append(
            {
                "code": "deploy_unverified",
                "message": "Fleet deploy currency is unverified",
            }
        )
    if str(acceptance.get("verdict", "")) == "UNPROVEN":
        rows.append(
            {
                "code": "orders_unresolved",
                "message": "Orders submitted but not filled yet",
            }
        )
    breaches = acceptance.get("breaches", [])
    if isinstance(breaches, list):
        for breach in breaches:
            if isinstance(breach, Mapping) and breach.get("severity") == "warn":
                rows.append(
                    {
                        "code": "acceptance_warning",
                        "message": str(breach.get("detail", "Acceptance warning")),
                    }
                )
    return rows
