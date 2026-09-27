"""Replay one exported S237 session, stage-isolated, and name every difference.

Agent: tooling
Role: feed each stage its live inputs (never the replay's upstream, Trap 2), compare
      with the live outputs, and attach one cause and the clean flag to every row.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from scripts.replay_fidelity_causes import attribute, evidence
from scripts.replay_fidelity_layers import analyst_rows, pm_rows, scanner_rows
from scripts.replay_fidelity_stages import replay_analyst, replay_pm, replay_scanner

if TYPE_CHECKING:
    from scripts.replay_fidelity_git import DeployCheck
    from scripts.replay_fidelity_inputs import SessionInputs
    from scripts.replay_settings import ReplaySettings

STAGES = ("scanner", "analyst", "pm")


@dataclass(frozen=True)
class SessionResult:
    """One session's Layer 1 rows and which stages were compared and replayed."""

    rows: list[dict[str, Any]]
    compared: dict[str, bool] = field(default_factory=dict)
    replayed: dict[str, bool] = field(default_factory=dict)


def replay_session(
    inputs: SessionInputs, settings: ReplaySettings, deploy: DeployCheck
) -> SessionResult:
    """Replay the three stages on the session's live inputs and compare each."""
    payload = inputs.payload
    live_scan = payload.get("scanner") or {}
    live_analysis = payload.get("analyst") or {}
    live_pm = payload.get("pm") or {}
    recommendations = live_analysis.get("recommendation_set") or {}
    compared = {
        "scanner": bool(live_scan.get("candidate_set")),
        "analyst": bool(recommendations),
        "pm": bool(live_pm),
    }
    replays = {
        "scanner": replay_scanner(inputs, settings) if compared["scanner"] else None,
        "analyst": replay_analyst(inputs, settings) if compared["analyst"] else None,
        "pm": replay_pm(inputs, settings) if compared["pm"] else None,
    }
    by_stage = {
        "scanner": scanner_rows(inputs.session, live_scan, replays["scanner"])
        if compared["scanner"]
        else [],
        "analyst": analyst_rows(inputs.session, live_analysis, replays["analyst"])
        if compared["analyst"]
        else [],
        "pm": pm_rows(inputs.session, live_pm, recommendations, replays["pm"])
        if compared["pm"]
        else [],
    }
    found = evidence(
        deploy,
        inputs.not_persisted,
        payload,
        {position.ticker for position in inputs.held},
    )
    rows: list[dict[str, Any]] = []
    for stage in STAGES:
        replayed = replays[stage] is not None
        for row in by_stage[stage]:
            row["cause"] = attribute(row, replayed, found)
            row["clean"] = deploy.clean
            rows.append(row)
    return SessionResult(
        rows,
        compared,
        {stage: compared[stage] and replays[stage] is not None for stage in STAGES},
    )
