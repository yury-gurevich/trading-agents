"""Deliberation eval — score a debate against a known-flaw answer key.

Agent: kernel
Role: turn a debate result into a deterministic pass/fail against an EvalCase
      (the flaw the debate should surface + the verdict it should reach), so the
      deliberation can be measured *without* waiting for live trade outcomes
      (DL-23 Path B — our documented gaps are the answer key). Decision-agnostic:
      the trading cases live in the caller, not here (platform/pack wall).
External I/O: none directly (deliberate() reaches the model via its injected client).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from kernel.deliberation import deliberate

if TYPE_CHECKING:
    from kernel.deliberation import DebateResult, Proposition
    from kernel.llm import LLMClient


@dataclass(frozen=True)
class EvalCase:
    """A decision whose right answer we know — the answer key for one debate.

    ``flaw_keywords``: at least one must appear in the Challenger's turns for the
    flaw to count as *caught*. ``expect_not_uphold``: a flawed decision should be
    overturned or revised, never upheld.
    """

    name: str
    proposition: Proposition
    flaw_keywords: tuple[str, ...]
    expect_not_uphold: bool = True


@dataclass(frozen=True)
class EvalScore:
    """The deterministic score of one debate against its EvalCase."""

    name: str
    flaw_caught: bool
    verdict_aligned: bool
    passed: bool


def score_debate(result: DebateResult, case: EvalCase) -> EvalScore:
    """Did the Challenger surface the flaw, and did the verdict align with the key?"""
    challenger = " ".join(
        turn.text for turn in result.transcript if turn.role == "challenger"
    ).lower()
    flaw_caught = any(keyword.lower() in challenger for keyword in case.flaw_keywords)
    upheld = result.verdict.ruling == "uphold"
    verdict_aligned = (not upheld) if case.expect_not_uphold else upheld
    return EvalScore(
        name=case.name,
        flaw_caught=flaw_caught,
        verdict_aligned=verdict_aligned,
        passed=flaw_caught and verdict_aligned,
    )


def run_eval(
    llm: LLMClient, cases: tuple[EvalCase, ...], *, max_rounds: int = 2
) -> tuple[EvalScore, ...]:
    """Run the debate on each case and score it — the manufactured eval pass."""
    return tuple(
        score_debate(deliberate(llm, case.proposition, max_rounds=max_rounds), case)
        for case in cases
    )


def pass_rate(scores: tuple[EvalScore, ...]) -> float:
    """Fraction of cases that passed (flaw caught AND verdict aligned)."""
    if not scores:
        return 0.0
    return sum(1 for score in scores if score.passed) / len(scores)
