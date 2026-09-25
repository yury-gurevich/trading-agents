"""Dashboard status-line vital for the book against the market.

Agent: surfaces
Role: colour and word the selected run's scoreboard; print the reporter's numbers only.
External I/O: injected GraphStore reads only.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from surfaces.queries.performance import run_performance
from surfaces.queries.performance_text import (
    detail_rows,
    display,
    summary,
    vital_line,
)

if TYPE_CHECKING:
    from kernel import GraphStore
    from surfaces.dashboard.settings import DashboardSettings

_IDLE_TEXT = {
    "unavailable": "no scoreboard for this run",
    "no_sessions": "no scoreboard sessions yet",
}


def performance_tone(excess: float, settings: DashboardSettings) -> str:
    """Green at or above zero, red at or below the red line, amber between (DL-220).

    Decided on the rounded number the operator reads, so a displayed 0.00 is green.
    """
    shown = display(excess)
    if shown >= 0:
        return "good"
    if shown <= -settings.performance_behind_threshold_pts:
        return "crit"
    return "warn"


def performance_vital(
    graph: GraphStore, run_id: str, settings: DashboardSettings
) -> dict[str, object]:
    """Return the vital for one run; unavailable carries no number at all."""
    view = run_performance(graph, run_id)
    if view.status != "measured":
        return {
            "run_id": run_id,
            "status": view.status,
            "tone": "idle",
            "text": _IDLE_TEXT[view.status],
            "reason": view.reason,
        }
    return {
        "run_id": run_id,
        "status": view.status,
        "tone": performance_tone(view.metrics["excess_return_pct"], settings),
        "text": vital_line(view),
        "detail": [list(row) for row in detail_rows(view)],
        "summary": summary(view),
    }
