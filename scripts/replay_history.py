"""The replay's visible window and its opt-in history rule (S250).

Agent: tooling
Role: slice a session's declared window; withhold unheld lines short of the bar.
External I/O: none.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import TYPE_CHECKING

from scripts.replay_series import window_bars

from agents.analyst.history_requirements import required_history_bars
from orchestration.history_window import declared_lookback_days

if TYPE_CHECKING:
    from collections.abc import Collection
    from datetime import date

    from scripts.replay_settings import ReplaySettings
    from scripts.sp500_bars import BarRow


@dataclass(frozen=True)
class OfferedLines:
    """The members a session offers, their bars, and how many were withheld."""

    members: tuple[str, ...]
    bars: tuple[BarRow, ...]
    removed: int


def visible_window(
    settings: ReplaySettings,
    line_bars: dict[str, tuple[BarRow, ...]],
    members: tuple[str, ...],
    session: date,
) -> tuple[BarRow, ...]:
    """Every member bar inside the lookback a fleet run declares for `session`."""
    lookback_days = declared_lookback_days(
        settings.analyst,
        as_of=session,
        staleness_buffer_sessions=settings.provider.max_staleness_days,
    )
    return window_bars(line_bars, members, session, lookback_days)


def offer_lines(
    settings: ReplaySettings,
    members: tuple[str, ...],
    rows: tuple[BarRow, ...],
    held_lines: Collection[str],
) -> OfferedLines:
    """Keep a held line, or one whose window holds the required bars (DL-258 D1)."""
    required = required_history_bars(settings.analyst)
    counts = Counter(row.line for row in rows)
    kept = tuple(
        line for line in members if line in held_lines or counts[line] >= required
    )
    keep = frozenset(kept)
    return OfferedLines(
        kept,
        tuple(row for row in rows if row.line in keep),
        len(members) - len(kept),
    )
