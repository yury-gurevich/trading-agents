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


def pass_fractions(runs: tuple[tuple[EvalScore, ...], ...]) -> dict[str, float]:
    """Per-case fraction of N runs that passed — the noise-aware competence signal."""
    if not runs:
        return {}
    counts: dict[str, int] = {}
    for run in runs:
        for score in run:
            counts[score.name] = counts.get(score.name, 0) + int(score.passed)
    return {name: count / len(runs) for name, count in counts.items()}


def robust_passing(
    runs: tuple[tuple[EvalScore, ...], ...], *, threshold: float = 0.5
) -> frozenset[str]:
    """Cases that passed in at least ``threshold`` of the N runs — robust to noise."""
    return frozenset(
        name for name, frac in pass_fractions(runs).items() if frac >= threshold
    )


@dataclass(frozen=True)
class BaselineCheck:
    """A candidate model's eval scores judged against the golden baseline."""

    regressed: tuple[str, ...]  # golden passed, candidate failed — the firewall trips
    gained: tuple[str, ...]  # candidate passed, golden did not — informational
    passed: bool  # no regressions


def _compare(
    candidate: frozenset[str], golden_passing: frozenset[str]
) -> BaselineCheck:
    """Diff a candidate competence set against the golden — the gate verdict."""
    regressed = tuple(sorted(golden_passing - candidate))
    gained = tuple(sorted(candidate - golden_passing))
    return BaselineCheck(regressed=regressed, gained=gained, passed=not regressed)


def check_baseline(
    candidate: tuple[EvalScore, ...], golden_passing: frozenset[str]
) -> BaselineCheck:
    """Single-run gate: trip iff the candidate regressed on a golden-passed case."""
    return _compare(passing_names(candidate), golden_passing)


def check_robust(
    candidate_runs: tuple[tuple[EvalScore, ...], ...],
    golden_passing: frozenset[str],
    *,
    threshold: float = 0.5,
) -> BaselineCheck:
    """N-run gate (EXP-006): trip only on a regression that persists across runs."""
    return _compare(robust_passing(candidate_runs, threshold=threshold), golden_passing)
