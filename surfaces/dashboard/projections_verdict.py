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
from surfaces.dashboard.projections_vitals import vitals_projection

if TYPE_CHECKING:
    from datetime import datetime

    from kernel import GraphStore
    from surfaces.dashboard.azure_port import AzureReader
    from surfaces.dashboard.settings import DashboardSettings


def verdict_projection(
    graph: GraphStore,
    run_id: str,
    azure: AzureReader | None,
    settings: DashboardSettings,
    *,
    now: datetime | None = None,
) -> dict[str, object]:
    """Read existing evidence and project the selected run's master verdict."""
    acceptance = run_verdict(graph, run_id)
    stages = run_stages(graph, run_id)
    vitals = vitals_projection(graph, azure, settings, run_id, now=now)
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
    light = "GREEN" if verdict in {"PASS", "NO_TRADE"} and not faults else "RED"
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
    for code, label in (("spine", "Graph spine"), ("bus", "Activation bus")):
        if _nested_value(vitals, code, "unavailable", key="status") != "reachable":
            faults.append({"code": code, "message": f"{label} is unreachable"})
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
    if pending:
        rows.append({"code": "pending_flags", "message": f"{pending} pending flags"})
    if degraded:
        rows.append({"code": "degraded_feeds", "message": f"{degraded} degraded feeds"})
    if isinstance(untracked, list) and untracked:
        rows.append(
            {"code": "untracked_spend", "message": "Some model spend is untracked"}
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


def _summary(
    verdict: str,
    stages: list[dict[str, object]],
    faults: list[dict[str, str]],
    *,
    confidence_bar: object = None,
) -> str:
    missing = _missing_stage(stages)
    if missing is not None:
        complete = sum(bool(stage.get("reached")) for stage in stages)
        return (
            f"Run stopped before {missing} — {complete}/{len(stages)} stages completed."
        )
    non_acceptance = next(
        (fault["message"] for fault in faults if fault["code"] != "acceptance"), None
    )
    if non_acceptance is not None:
        return f"Attention needed: {non_acceptance.lower()}."
    if verdict == "NO_TRADE":
        rejected = _observed(stages, "analyst", "rejected")
        noun = "candidate" if rejected == 1 else "candidates"
        bar = (
            f" ({float(confidence_bar):g})"
            if isinstance(confidence_bar, int | float)
            else ""
        )
        return f"{rejected} {noun} below confidence bar{bar}"
    if verdict == "PASS":
        scored = _observed(stages, "analyst", "scored")
        submitted = _observed(stages, "execution", "submitted")
        order_noun = "order" if submitted == 1 else "orders"
        candidate_noun = "candidate" if scored == 1 else "candidates"
        return f"{submitted} {order_noun}, {scored} {candidate_noun}"
    return "Acceptance failed."


def _missing_stage(stages: list[dict[str, object]]) -> str | None:
    row = next((stage for stage in stages if not stage.get("reached")), None)
    return str(row["name"]) if row is not None else None


def _observed(stages: list[dict[str, object]], name: str, key: str) -> int:
    row = next((stage for stage in stages if stage.get("name") == name), {})
    observed = row.get("observed", {})
    return _as_int(observed.get(key) if isinstance(observed, Mapping) else 0)


def _nested_value(
    source: Mapping[str, object], name: str, default: object, *, key: str | None = None
) -> object:
    value = source.get(name, default)
    if key is not None:
        return value.get(key, default) if isinstance(value, Mapping) else default
    return value


def _as_int(value: object) -> int:
    return int(value) if isinstance(value, (int, float)) else 0
