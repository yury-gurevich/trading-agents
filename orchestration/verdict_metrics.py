"""Agreement metrics over replayed and recorded verdicts.

Agent: orchestration
Role: answer "does the veto agree with itself" — and with a second vendor, and
      with the hand-checked ground truth — from verdict labels, never prose.
External I/O: reads the injected GraphStore for recorded verdicts. No writes.

One exclusion predicate, in one place: a fail-open is recorded as
``verdict: "uphold"`` (``review_record.fail_open_review``), so a metric that does
not subtract ``failed_open_tickers`` measures the fail-open rate and calls it
agreement. DL-104's run D is 5 of 6, not 5 of 10, for exactly this reason.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from itertools import combinations
from typing import TYPE_CHECKING

from orchestration.agreement import Agreement

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

    from kernel import GraphStore

__all__ = [
    "ReplayVerdict",
    "agreement_with",
    "real_verdicts",
    "recorded_verdicts",
    "self_agreement",
]

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


def real_verdicts(props: Mapping[str, object]) -> dict[str, str]:
    """Read one DeliberationRun's verdicts with its fail-opens subtracted."""
    # The in-memory store freezes props (dict -> mappingproxy, list -> tuple) while
    # the Postgres store returns plain JSON types, so both shapes must be read.
    verdicts = props.get("verdicts")
    if not isinstance(verdicts, Mapping):
        return {}
    failed = props.get("failed_open_tickers")
    excluded = set(failed) if isinstance(failed, list | tuple) else set()
    return {
        str(ticker): str(ruling)
        for ticker, ruling in verdicts.items()
        if ticker not in excluded
    }


def recorded_verdicts(graph: GraphStore) -> dict[Decision, str]:
    """Every real verdict the live fleet has recorded, fail-opens removed."""
    found: dict[Decision, str] = {}
    for node in graph.list_nodes("DeliberationRun"):
        for ticker, ruling in real_verdicts(node.props).items():
            found[(node.key, ticker)] = ruling
    return found


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
    name = "self_agreement" if arm is None else f"self_agreement[{arm}]"
    return Agreement(
        name=name,
        matched=sum(1 for first, second in pairs if first == second),
        compared=len(pairs),
        excluded=excluded,
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
