"""Deliberation eval tests — scoring a debate against a known-flaw answer key.

Agent: kernel
Role: verify score_debate (flaw-caught + verdict-aligned), run_eval, and pass_rate
      deterministically, so the deliberation can be measured without trade outcomes.
External I/O: none.
"""

from __future__ import annotations

from kernel import (
    DebateResult,
    EvalCase,
    LLMJudgeScorer,
    Proposition,
    Turn,
    Verdict,
    pass_rate,
    run_debates,
    run_eval,
    score_debate,
)

_CASE = EvalCase(
    name="concentration",
    proposition=Proposition(decision="Buy NVDA", context="semis-heavy book"),
    flaw_keywords=("correlation", "concentration", "crowded"),
    flaw="adding NVDA concentrates the book in correlated semiconductors",
)


def _result(challenger: str, ruling: str) -> DebateResult:
    transcript = (
        Turn("defender", 1, "for it"),
        Turn("challenger", 1, challenger),
    )
    return DebateResult(_CASE.proposition, transcript, Verdict(ruling, "—"))


def test_pass_when_flaw_caught_and_not_upheld() -> None:
    score = score_debate(
        _result("this adds correlation risk to a crowded book", "overturn"), _CASE
    )
    assert score.flaw_caught
    assert score.verdict_aligned
    assert score.passed


def test_fail_when_upheld_even_if_flaw_caught() -> None:
    score = score_debate(_result("concentration risk noted", "uphold"), _CASE)
    assert score.flaw_caught
    assert not score.verdict_aligned
    assert not score.passed


def test_fail_when_flaw_missed() -> None:
    score = score_debate(_result("the stop is too tight", "revise"), _CASE)
    assert not score.flaw_caught
    assert score.verdict_aligned
    assert not score.passed


def test_expect_uphold_case_aligns_on_uphold() -> None:
    case = EvalCase(
        name="sound",
        proposition=Proposition(decision="Buy Y", context="z"),
        flaw_keywords=("x",),
        expect_not_uphold=False,
    )
    score = score_debate(_result("x is fine", "uphold"), case)
    assert score.verdict_aligned


class _Fake:
    """Role-routing fake: Challenger raises the flaw, Judge overturns."""

    def complete(
        self, *, system: str, user: str, tool_schema: dict[str, object]
    ) -> str:
        del user, tool_schema
        if "DEFENDER" in system:
            return "buy it"
        if "CHALLENGER" in system:
            return "this adds correlation risk to a crowded semis book"
        return '{"ruling": "overturn", "rationale": "correlated concentration"}'


def test_run_eval_and_pass_rate() -> None:
    scores = run_eval(_Fake(), (_CASE,), max_rounds=1)
    assert len(scores) == 1
    assert scores[0].passed
    assert pass_rate(scores) == 1.0


def test_run_debates_returns_one_result_per_case() -> None:
    debates = run_debates(_Fake(), (_CASE, _CASE), max_rounds=1)
    assert len(debates) == 2
    assert all(isinstance(d, DebateResult) for d in debates)


def test_run_debates_passes_dedicated_debate_judge() -> None:
    debates = run_debates(
        _Fake(),
        (_CASE,),
        max_rounds=1,
        judge_llm=_JudgeFake('{"ruling": "revise", "rationale": "dedicated"}'),
    )

    assert debates[0].verdict.ruling == "revise"
    assert debates[0].verdict.rationale == "dedicated"


def test_pass_rate_empty_is_zero() -> None:
    assert pass_rate(()) == 0.0


class _JudgeFake:
    """Judge stub returning a fixed scorer reply regardless of the argument."""

    def __init__(self, reply: str) -> None:
        self._reply = reply

    def complete(
        self, *, system: str, user: str, tool_schema: dict[str, object]
    ) -> str:
        del system, user, tool_schema
        return self._reply


def test_llm_judge_caught_and_aligned() -> None:
    scorer = LLMJudgeScorer(_JudgeFake('{"caught": true}'))
    score = scorer(_result("vague worry", "overturn"), _CASE)
    assert score.flaw_caught
    assert score.passed


def test_llm_judge_not_caught() -> None:
    scorer = LLMJudgeScorer(_JudgeFake('{"caught": false}'))
    score = scorer(_result("this names the exact flaw", "overturn"), _CASE)
    assert not score.flaw_caught
    assert not score.passed


def test_llm_judge_caught_but_upheld_not_aligned() -> None:
    scorer = LLMJudgeScorer(_JudgeFake('{"caught": true}'))
    score = scorer(_result("caught it", "uphold"), _CASE)
    assert score.flaw_caught
    assert not score.verdict_aligned
    assert not score.passed


def test_llm_judge_unparseable_is_not_caught() -> None:
    scorer = LLMJudgeScorer(_JudgeFake("not json"))
    score = scorer(_result("anything", "overturn"), _CASE)
    assert not score.flaw_caught
