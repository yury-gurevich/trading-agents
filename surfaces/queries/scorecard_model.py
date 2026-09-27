"""The unattended scorecard's result: its sessions, the goals' shares and both clocks.

Agent: surfaces
Role: hold one window's sessions and derive G1, G3 and the two clocks from them.
External I/O: none.

Every number is a count over the sessions `surfaces.queries.scorecard` read from the
graph; nothing here reads, judges or rounds. "Complete" is the gate's word (PASS or
NO_TRADE), never `.passed`, which is true for UNPROVEN (DL-59).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Literal

from surfaces.queries.scorecard_actions import DEPLOY
from surfaces.queries.scorecard_verdicts import COMPLETE

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping
    from datetime import date

    from surfaces.scorecard_settings import ScorecardSettings

ScorecardStatus = Literal["measured", "unavailable"]


@dataclass(frozen=True)
class SessionRow:
    """One counted session: the gate's word and the human actions placed on it."""

    day: date
    run_id: str
    verdict: str
    actions: Mapping[str, int] = field(default_factory=dict)

    @property
    def complete(self) -> bool:
        """The run completed: its word is PASS or NO_TRADE, never merely `.passed`."""
        return self.verdict in COMPLETE

    @property
    def acted(self) -> bool:
        """A human acted on the run: any action but a deploy."""
        return any(kind != DEPLOY for kind in self.actions)

    @property
    def touched(self) -> bool:
        """Anything human reached the run, a deploy included."""
        return bool(self.actions)


@dataclass(frozen=True)
class Scorecard:
    """The window's sessions and the goals' numbers, or why there are none.

    ``streak`` holds sessions before the window as well, read only when the whole
    window holds and the clocks' target is longer than it (DL-235 amendment); G1 and
    G3 never see it.
    """

    status: ScorecardStatus
    settings: ScorecardSettings
    sessions: tuple[SessionRow, ...] = ()
    reason: str = ""
    streak: tuple[SessionRow, ...] = ()

    @property
    def counted(self) -> int:
        """Sessions in the window whose dispatcher window has closed."""
        return len(self.sessions)

    @property
    def complete(self) -> int:
        """Counted sessions whose run completed."""
        return sum(row.complete for row in self.sessions)

    @property
    def healthy(self) -> int:
        """G3's denominator: a healthy session is a complete one."""
        return self.complete

    @property
    def hands_on(self) -> int:
        """Healthy sessions a human acted on (G3's numerator; deploys aside)."""
        return sum(row.complete and row.acted for row in self.sessions)

    @property
    def hands_on_with_deploys(self) -> int:
        """Healthy sessions anything human reached, deploys included."""
        return sum(row.complete and row.touched for row in self.sessions)

    @property
    def g1(self) -> float | None:
        """Complete over counted sessions."""
        return _share(self.complete, self.counted)

    @property
    def g3(self) -> float | None:
        """Hands-on over healthy sessions; None when no session was healthy."""
        return _share(self.hands_on, self.healthy)

    @property
    def g3_with_deploys(self) -> float | None:
        """The same share, counting deploys as a human touch."""
        return _share(self.hands_on_with_deploys, self.healthy)

    @property
    def unattended(self) -> int:
        """Latest sessions in a row that completed with no human action but deploys."""
        return _run_back(self._clock_rows, lambda row: row.complete and not row.acted)

    @property
    def untouched(self) -> int:
        """Latest sessions in a row that completed with nothing human at all."""
        return _run_back(self._clock_rows, lambda row: row.complete and not row.touched)

    @property
    def _clock_rows(self) -> tuple[SessionRow, ...]:
        return self.streak or self.sessions


def _share(part: int, whole: int) -> float | None:
    return part / whole if whole else None


def _run_back(rows: tuple[SessionRow, ...], holds: Callable[[SessionRow], bool]) -> int:
    """Count back from the latest session; the first that does not hold stops it."""
    count = 0
    for row in reversed(rows):
        if not holds(row):
            break
        count += 1
    return count
