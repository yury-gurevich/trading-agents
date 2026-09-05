"""Agreement metrics over replayed and recorded verdicts.

Agent: orchestration
Role: answer "does the veto agree with itself" — and with a second vendor, and
      with the hand-checked ground truth — from verdict labels, never prose.
External I/O: none — the records come from a replay sweep or from
              ``orchestration.verdict_sources``.

Every metric counts three things separately: what agreed, what was excluded
because no real debate produced it, and what had nothing to be compared against.
Collapsing the last two would let a shrinking overlap read as a rising failure
rate, which is the shape of error this sprint exists to remove.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import TYPE_CHECKING

from orchestration.agreement import Agreement

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence

__all__ = ["Decision", "ReplayVerdict", "agreement_with", "self_agreement"]

Decision = tuple[str, str]


@dataclass(frozen=True)
class ReplayVerdict:
    """One replayed debate's outcome, or the reason it produced none."""

    pm_run: str
    ticker: str
    arm: str
    repeat: int
    ruling: str | None = None
    failure: str | None = None

    @property
    def decision(self) -> Decision:
        """The (run, ticker) pair this verdict is about."""
        return (self.pm_run, self.ticker)

    @property
    def usable(self) -> bool:
        """A verdict is comparable only when a real debate produced it."""
        return self.failure is None and self.ruling is not None


def self_agreement(
    verdicts: Iterable[ReplayVerdict], *, arm: str | None = None
) -> Agreement:
    """Compare every repeat of one decision against every other repeat of it."""
    usable, excluded = _split(verdicts, arm)
    grouped: dict[Decision, list[str]] = {}
    for verdict in usable:
        grouped.setdefault(verdict.decision, []).append(str(verdict.ruling))
    pairs = [
        (first, second)
        for rulings in grouped.values()
        for first, second in combinations(rulings, 2)
    ]
    return Agreement(
        name="self_agreement" if arm is None else f"self_agreement[{arm}]",
        matched=sum(1 for first, second in pairs if first == second),
        compared=len(pairs),
        excluded=excluded,
        # A decision replayed only once yields no pair. It is not a failure and
        # not a disagreement, but it must not vanish from the report either.
        no_counterpart=sum(
            len(rulings) for rulings in grouped.values() if len(rulings) < 2
        ),
    )


def agreement_with(
    verdicts: Iterable[ReplayVerdict],
    truth: Mapping[Decision, str],
    *,
    name: str,
    arm: str | None = None,
) -> Agreement:
    """Compare each usable replayed verdict against a second source's ruling."""
    usable, excluded = _split(verdicts, arm)
    comparable = [verdict for verdict in usable if verdict.decision in truth]
    return Agreement(
        name=name if arm is None else f"{name}[{arm}]",
        matched=sum(
            1 for verdict in comparable if verdict.ruling == truth[verdict.decision]
        ),
        compared=len(comparable),
        excluded=excluded,
        no_counterpart=len(usable) - len(comparable),
    )


def _split(
    verdicts: Iterable[ReplayVerdict], arm: str | None
) -> tuple[Sequence[ReplayVerdict], int]:
    selected = [verdict for verdict in verdicts if arm is None or verdict.arm == arm]
    usable = [verdict for verdict in selected if verdict.usable]
    return usable, len(selected) - len(usable)
