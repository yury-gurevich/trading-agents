"""Dashboard status-line tile: how long the pack has run without a human.

Agent: surfaces
Role: colour and word the scorecard's window for the tile; no run scopes a window.
External I/O: injected GraphStore reads only, through the scorecard query.

Served by its own route, never inside `/api/vitals`: its first read judges every
unbriefed run in the window, which must not hold the other vitals (DL-235).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from surfaces.queries.scorecard import scorecard
from surfaces.queries.scorecard_actions import PLACED_LABELS, ScorecardDataError
from surfaces.queries.scorecard_text import (
    NOT_COUNTED,
    detail_rows,
    session_rows,
    summary,
    tone,
    vital_line,
)

if TYPE_CHECKING:
    from kernel import GraphStore
    from surfaces.scorecard_settings import ScorecardSettings

_UNREADABLE = "the graph could not be read"
# The page hears a fixed sentence chosen by the record's kind, never an exception's
# text (SRF-SEC-02; CodeQL py/stack-trace-exposure, alerts 256 and 257).
_UNPLACEABLE = {
    label: f"one {label} carries no readable time" for label in PLACED_LABELS
}
_UNPLACEABLE_OTHER = "a stored record carries no readable time"


def scorecard_vital(
    graph: GraphStore, settings: ScorecardSettings, *, now: datetime | None = None
) -> dict[str, object]:
    """Return the tile for the window ending ``now``; unavailable shows no number."""
    try:
        card = scorecard(graph, now=now or datetime.now(tz=UTC), settings=settings)
    except ScorecardDataError as exc:  # names a kind of record, never a stored value
        return _unavailable(_unplaceable(exc.label))
    except Exception:  # an unreadable graph degrades the tile, never the page
        return _unavailable(_UNREADABLE)
    if card.status != "measured":
        return _unavailable(card.reason)
    return {
        "status": card.status,
        "tone": tone(card),
        "text": vital_line(card),
        "detail": [list(row) for row in detail_rows(card)],
        "sessions": [list(row) for row in session_rows(card)],
        "not_counted": list(NOT_COUNTED),
        "summary": summary(card),
    }


def _unplaceable(label: str) -> str:
    """The fixed sentence for ``label``: matched against the table, never echoed."""
    for known, sentence in _UNPLACEABLE.items():
        if known == label:
            return sentence
    return _UNPLACEABLE_OTHER


def _unavailable(reason: str) -> dict[str, object]:
    return {
        "status": "unavailable",
        "tone": "idle",
        "text": "unattended: unavailable",
        "reason": reason,
    }
