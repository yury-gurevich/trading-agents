"""The value types one replayed debate is made of.

Agent: orchestration
Role: name an arm, a stored decision, a batch request/answer, and the running
      state of one replayed debate — with no behaviour beyond identity.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from orchestration.replay_keys import JUDGE_ROUND, ReplayKey

if TYPE_CHECKING:
    from kernel.deliberation import Proposition, Turn, Verdict

__all__ = [
    "ARGUING_ROLES",
    "JUDGE_ROLE",
    "Arm",
    "BatchRequest",
    "BatchResult",
    "DebateState",
    "ReplaySubject",
    "Step",
]

ARGUING_ROLES = ("defender", "challenger")
JUDGE_ROLE = "judge"

Step = tuple[str, int]


@dataclass(frozen=True)
class Arm:
    """One configuration under test: what the sweep actually varies."""

    name: str
    model: str
    effort: str
    max_rounds: int
    max_tokens: int = 4096

    def steps(self) -> tuple[Step, ...]:
        """The turns this arm speaks, in order, judge last."""
        turns: list[Step] = [
            (role, number)
            for number in range(1, max(1, self.max_rounds) + 1)
            for role in ARGUING_ROLES
        ]
        turns.append((JUDGE_ROLE, JUDGE_ROUND))
        return tuple(turns)


@dataclass(frozen=True)
class ReplaySubject:
    """One stored decision, rebuilt from the graph and ready to re-debate."""

    pm_run: str
    ticker: str
    proposition: Proposition


@dataclass(frozen=True)
class BatchRequest:
    """One model call, addressed by its wire id."""

    custom_id: str
    model: str
    max_tokens: int
    effort: str
    system: str
    user: str


@dataclass(frozen=True)
class BatchResult:
    """One answer, or a named reason there is none."""

    custom_id: str
    status: str
    text: str = ""


@dataclass
class DebateState:
    """The running transcript for one (subject, repeat, arm) debate."""

    subject: ReplaySubject
    repeat: int
    arm: Arm
    transcript: tuple[Turn, ...] = ()
    verdict: Verdict | None = None
    failure: str | None = None
    steps: tuple[Step, ...] = field(default_factory=tuple)

    def key(self, step: Step) -> ReplayKey:
        """The identity of this debate's turn at ``step``."""
        role, number = step
        return ReplayKey(
            pm_run=self.subject.pm_run,
            ticker=self.subject.ticker,
            repeat=self.repeat,
            arm=self.arm.name,
            role=role,
            round=number,
        )
