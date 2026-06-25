"""Deliberation gate — judge an eval run against a frozen golden baseline.

Agent: kernel
Role: the DL-24 model-swap regression gate. Given a candidate model's eval scores
      and the champion's golden *passing set*, flag the cases that REGRESSED
      (golden passed, candidate failed) so a model downgrade/side-grade cannot
      silently lower debate quality. Pure set logic; decision-agnostic — the
      golden baseline (trading cases) lives in the caller (platform/pack wall).
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kernel.deliberation_eval import EvalScore


def passing_names(scores: tuple[EvalScore, ...]) -> frozenset[str]:
    """The names of the cases a model passed — its demonstrated competence set."""
    return frozenset(score.name for score in scores if score.passed)


@dataclass(frozen=True)
class BaselineCheck:
    """A candidate model's eval scores judged against the golden baseline."""

    regressed: tuple[str, ...]  # golden passed, candidate failed — the firewall trips
    gained: tuple[str, ...]  # candidate passed, golden did not — informational
    passed: bool  # no regressions


def check_baseline(
    candidate: tuple[EvalScore, ...], golden_passing: frozenset[str]
) -> BaselineCheck:
    """Trip the gate iff the candidate regressed on any case the golden passed."""
    cand = passing_names(candidate)
    regressed = tuple(sorted(golden_passing - cand))
    gained = tuple(sorted(cand - golden_passing))
    return BaselineCheck(regressed=regressed, gained=gained, passed=not regressed)
