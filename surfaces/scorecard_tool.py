"""The "running unattended" tool: how long the pack has run without a human.

Agent: surfaces
Role: answer G1, G3 and both clocks from the graph, for MCP and the chat's quick ask.
External I/O: injected GraphStore reads only; no bus request, no model (SRF-OUT-08).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from surfaces.queries.scorecard import scorecard
from surfaces.queries.scorecard_text import NOT_COUNTED, summary
from surfaces.scorecard_settings import ScorecardSettings

if TYPE_CHECKING:
    from surfaces.context import SurfaceContext
    from surfaces.queries.scorecard_model import Scorecard

ToolResult = dict[str, object]


def utc_now() -> datetime:
    """Return the instant the window ends at: now, in UTC."""
    return datetime.now(tz=UTC)


def scorecard_tool(ctx: SurfaceContext, args: ToolResult) -> ToolResult:
    """Return the window's numbers and the answer; no run scopes a window."""
    del args  # the scorecard is a window of sessions, never one run (SRF-OUT-08)
    return answer(scorecard(ctx.graph, now=utc_now(), settings=ScorecardSettings()))


def answer(card: Scorecard) -> ToolResult:
    """Return the numbers the tile shows and the one answer the chat also gives."""
    if card.status != "measured":
        return {"status": card.status, "reason": card.reason, "summary": summary(card)}
    goals = card.settings
    return {
        "status": card.status,
        "window_days": goals.scorecard_window_days,
        "sessions": card.counted,
        "complete": card.complete,
        "g1": card.g1,
        "g1_target": goals.scorecard_g1_target,
        "healthy": card.healthy,
        "hands_on": card.hands_on,
        "hands_on_with_deploys": card.hands_on_with_deploys,
        "g3": card.g3,
        "g3_with_deploys": card.g3_with_deploys,
        "g3_target": goals.scorecard_g3_target,
        "unattended": card.unattended,
        "untouched": card.untouched,
        "clock_target": goals.scorecard_clock_sessions,
        "rows": [
            {
                "date": row.day.isoformat(),
                "run_id": row.run_id,
                "verdict": row.verdict,
                "complete": row.complete,
                "actions": dict(row.actions),
            }
            for row in card.sessions
        ],
        "not_counted": list(NOT_COUNTED),
        "summary": summary(card),
    }
