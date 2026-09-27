"""One named cause for every S237 Layer 1 difference.

Agent: tooling
Role: attribute a difference to not-replayed, changed code, a named export gap, or
      nothing; in that order, exactly one per difference.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Mapping

    from scripts.replay_fidelity_git import DeployCheck

NOT_REPLAYED = "harness:not_replayed"
UNEXPLAINED = "unexplained"
# A held-stop threshold changes only the stop-exit fields of a held name (DL-238 D4).
_STOP_FIELDS = frozenset({"action", "exit_trigger"})


@dataclass(frozen=True)
class Evidence:
    """What a session's export says the replay could not have been given."""

    deploy: DeployCheck
    gaps: frozenset[str]
    held: frozenset[str]
    stop_exits: frozenset[str]


def evidence(
    deploy: DeployCheck,
    gaps: frozenset[str],
    payload: Mapping[str, Any],
    held: set[str],
) -> Evidence:
    """Collect the live held names and live stop exits the gap rules need."""
    candidates = {
        str(item.get("ticker"))
        for item in (payload.get("scanner") or {})
        .get("candidate_set", {})
        .get("candidates", ())
    }
    recommendations = (payload.get("analyst") or {}).get("recommendation_set") or {}
    live = recommendations.get("recommendations") or ()
    analysed = {str(item.get("ticker")) for item in live} | {
        str(item.get("ticker")) for item in recommendations.get("rejections") or ()
    }
    held_live = {str(item["ticker"]) for item in live if item.get("action") != "buy"}
    return Evidence(
        deploy=deploy,
        gaps=gaps,
        held=frozenset(held | held_live | (analysed - candidates)),
        stop_exits=frozenset(
            str(item["ticker"]) for item in live if item.get("exit_trigger") == "stop"
        ),
    )


def attribute(row: Mapping[str, Any], replayed: bool, found: Evidence) -> str:
    """Return the one cause of a differing row ("" for a match)."""
    if row["match"]:
        return ""
    if not replayed:
        return NOT_REPLAYED
    if not found.deploy.clean:
        return f"code_changed:{found.deploy.path_for(str(row['stage']))}"
    gap = _gap(row, found)
    return f"not_persisted:{gap}" if gap else UNEXPLAINED


def _gap(row: Mapping[str, Any], found: Evidence) -> str | None:
    stage, ticker = str(row["stage"]), str(row["ticker"])
    if (
        "held_stops" in found.gaps
        and stage == "analyst"
        and ticker in found.stop_exits
        and row["field"] in _STOP_FIELDS
    ):
        return "held_stops"
    if "held_positions" in found.gaps and (
        stage == "pm" or (stage == "analyst" and ticker in found.held)
    ):
        return "held_positions"
    if "benchmark" in found.gaps and stage in ("scanner", "analyst"):
        return "benchmark"
    return None
