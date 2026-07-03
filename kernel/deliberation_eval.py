"""Deliberation eval — score a debate against a known-flaw answer key.

Agent: kernel
Role: turn a debate result into a pass/fail against an EvalCase (the flaw the
      debate should surface + the verdict it should reach), so the deliberation
      can be measured *without* waiting for live trade outcomes (DL-23 Path B —
      our documented gaps are the answer key). Two scorers: a deterministic
      keyword match (`score_debate`) and a semantic `LLMJudgeScorer` (EXP-004 —
      "did the Challenger identify THIS specific flaw?"). Decision-agnostic: the
      trading cases live in the caller, not here (platform/pack wall).
External I/O: none directly (deliberate / the judge reach the model via injected
clients).
"""

from __future__ import annotations

import json
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
    keyword scorer to count the flaw as *caught*. ``flaw``: the flaw stated in
    full, for the semantic ``LLMJudgeScorer``. ``expect_not_uphold``: a flawed
    decision should be overturned or revised, never upheld.
    """

    name: str
    proposition: Proposition
    flaw_keywords: tuple[str, ...]
    flaw: str = ""
    expect_not_uphold: bool = True


@dataclass(frozen=True)
class EvalScore:
    """The score of one debate against its EvalCase."""

    name: str
    flaw_caught: bool
    verdict_aligned: bool
    passed: bool


def _verdict_aligned(result: DebateResult, case: EvalCase) -> bool:
    """A flawed case should not be upheld; a sound one should be."""
    upheld = result.verdict.ruling == "uphold"
    return (not upheld) if case.expect_not_uphold else upheld


def _challenger_text(result: DebateResult) -> str:
    """The Challenger's turns, joined — the case against the decision."""
    return " ".join(t.text for t in result.transcript if t.role == "challenger")


def score_debate(result: DebateResult, case: EvalCase) -> EvalScore:
    """Keyword scorer: did a flaw keyword appear, and did the verdict align?"""
    challenger = _challenger_text(result).lower()
    flaw_caught = any(kw.lower() in challenger for kw in case.flaw_keywords)
    aligned = _verdict_aligned(result, case)
    return EvalScore(case.name, flaw_caught, aligned, flaw_caught and aligned)


JUDGE_SCORER_SYSTEM = (
    "You are scoring a decision review. You are given the SPECIFIC FLAW the review "
    "should have surfaced and the CHALLENGER's argument. Did the challenger identify "
    "THIS specific flaw — not merely raise generic caution? "
    'Reply ONLY as JSON: {"caught": true} or {"caught": false}.'
)


def _parse_caught(raw: str) -> bool:
    """Parse the judge's JSON; an unreadable reply counts as *not caught*."""
    try:
        return bool(json.loads(raw)["caught"])
    except (json.JSONDecodeError, KeyError, TypeError):
        return False


@dataclass(frozen=True)
class LLMJudgeScorer:
    """Semantic scorer (EXP-004): an LLM rules if the Challenger caught the flaw."""

    judge: LLMClient

    def __call__(self, result: DebateResult, case: EvalCase) -> EvalScore:
        """Ask the judge if the Challenger identified the case's specific flaw."""
        user = f"SPECIFIC FLAW:\n{case.flaw}\n\nCHALLENGER:\n{_challenger_text(result)}"
        raw = self.judge.complete(system=JUDGE_SCORER_SYSTEM, user=user, tool_schema={})
        flaw_caught = _parse_caught(raw)
        aligned = _verdict_aligned(result, case)
        return EvalScore(case.name, flaw_caught, aligned, flaw_caught and aligned)


def run_debates(
    llm: LLMClient,
    cases: tuple[EvalCase, ...],
    *,
    max_rounds: int = 2,
    judge_llm: LLMClient | None = None,
) -> tuple[DebateResult, ...]:
    """Run the debate for each case once — so multiple scorers can share the result."""
    return tuple(
        deliberate(llm, case.proposition, max_rounds=max_rounds, judge_llm=judge_llm)
        for case in cases
    )


def run_eval(
    llm: LLMClient,
    cases: tuple[EvalCase, ...],
    *,
    max_rounds: int = 2,
    judge_llm: LLMClient | None = None,
) -> tuple[EvalScore, ...]:
    """Run + keyword-score each case — the manufactured eval pass."""
    debates = run_debates(llm, cases, max_rounds=max_rounds, judge_llm=judge_llm)
    return tuple(score_debate(d, c) for d, c in zip(debates, cases, strict=True))


def pass_rate(scores: tuple[EvalScore, ...]) -> float:
    """Fraction of cases that passed (flaw caught AND verdict aligned)."""
    if not scores:
        return 0.0
    return sum(1 for score in scores if score.passed) / len(scores)
