"""Deliberation harness tests — defend/attack/judge debate over a proposition.

Agent: kernel
Role: verify the bounded three-role debate produces a structured transcript and
      a parsed verdict, and that the Judge parser degrades safely.
External I/O: none.
"""

from __future__ import annotations

from kernel import (
    CHALLENGER_SYSTEM,
    DEFENDER_SYSTEM,
    JUDGE_SYSTEM,
    DeliberationPrompts,
    Proposition,
    deliberate,
)
from kernel.deliberation import _parse_verdict


class _RoleLLM:
    """Fake LLMClient that routes by the role-defining system prompt."""

    def __init__(self, defender: str, challenger: str, judge: str) -> None:
        self._defender = defender
        self._challenger = challenger
        self._judge = judge

    def complete(
        self, *, system: str, user: str, tool_schema: dict[str, object]
    ) -> str:
        del user, tool_schema
        if "DEFENDER" in system:
            return self._defender
        if "CHALLENGER" in system:
            return self._challenger
        return self._judge


class _RecordingLLM(_RoleLLM):
    """Role fake that records which system prompts were sent to it."""

    def __init__(self, defender: str, challenger: str, judge: str) -> None:
        super().__init__(defender, challenger, judge)
        self.systems: list[str] = []

    def complete(
        self, *, system: str, user: str, tool_schema: dict[str, object]
    ) -> str:
        self.systems.append(system)
        return super().complete(system=system, user=user, tool_schema=tool_schema)


_PROP = Proposition(decision="Buy AAPL", context="momentum 0.6; RSI 55")


def test_deliberate_produces_transcript_and_verdict() -> None:
    llm = _RoleLLM(
        defender="  The momentum supports it.  ",
        challenger="RSI is mid-range; weak edge.",
        judge='{"ruling": "revise", "rationale": "size it down"}',
    )
    result = deliberate(llm, _PROP, max_rounds=2)

    assert [t.role for t in result.transcript] == [
        "defender",
        "challenger",
        "defender",
        "challenger",
    ]
    assert [t.round for t in result.transcript] == [1, 1, 2, 2]
    assert result.transcript[0].text == "The momentum supports it."  # stripped
    assert result.verdict.ruling == "revise"
    assert result.verdict.rationale == "size it down"
    assert result.proposition is _PROP


def test_max_rounds_clamped_to_one() -> None:
    llm = _RoleLLM("for", "against", '{"ruling": "uphold", "rationale": "ok"}')
    result = deliberate(llm, _PROP, max_rounds=0)
    assert len(result.transcript) == 2  # one round: defender + challenger
    assert result.verdict.ruling == "uphold"


def test_dedicated_judge_llm_rules_the_debate() -> None:
    argue = _RecordingLLM(
        "for", "against", '{"ruling": "uphold", "rationale": "argue"}'
    )
    judge = _RecordingLLM(
        "unused", "unused", '{"ruling": "overturn", "rationale": "judge"}'
    )

    result = deliberate(argue, _PROP, max_rounds=1, judge_llm=judge)

    assert result.verdict.ruling == "overturn"
    assert result.verdict.rationale == "judge"
    assert len(argue.systems) == 2
    assert all("JUDGE" not in system for system in argue.systems)
    assert len(judge.systems) == 1
    assert "JUDGE" in judge.systems[0]


def test_without_dedicated_judge_llm_single_model_rules() -> None:
    llm = _RecordingLLM("for", "against", '{"ruling": "uphold", "rationale": "same"}')

    result = deliberate(llm, _PROP, max_rounds=1)

    assert result.verdict.ruling == "uphold"
    assert len(llm.systems) == 3
    assert "JUDGE" in llm.systems[-1]


def test_default_prompts_are_byte_identical_to_constants() -> None:
    llm = _RecordingLLM("for", "against", '{"ruling": "revise", "rationale": "same"}')

    deliberate(llm, _PROP, max_rounds=1)

    assert llm.systems == [DEFENDER_SYSTEM, CHALLENGER_SYSTEM, JUDGE_SYSTEM]


def test_role_prompt_overrides_are_used() -> None:
    llm = _RecordingLLM("for", "against", '{"ruling": "uphold", "rationale": "ok"}')
    prompts = DeliberationPrompts(
        defender="DEFENDER compiled prompt",
        challenger="CHALLENGER compiled prompt",
        judge="JUDGE compiled prompt",
    )

    result = deliberate(llm, _PROP, max_rounds=1, prompts=prompts)

    assert result.verdict.ruling == "uphold"
    assert llm.systems == [
        "DEFENDER compiled prompt",
        "CHALLENGER compiled prompt",
        "JUDGE compiled prompt",
    ]


def test_parse_verdict_valid() -> None:
    v = _parse_verdict('{"ruling": "OVERTURN", "rationale": "fatal risk"}')
    assert v.ruling == "overturn"  # lower-cased
    assert v.rationale == "fatal risk"


def test_parse_verdict_unparseable_defaults_to_revise() -> None:
    v = _parse_verdict("not json at all")
    assert v.ruling == "revise"
    assert "unparseable" in v.rationale


def test_parse_verdict_missing_ruling_defaults_to_revise() -> None:
    v = _parse_verdict('{"rationale": "no ruling key"}')
    assert v.ruling == "revise"


def test_parse_verdict_unrecognised_ruling_defaults_to_revise() -> None:
    v = _parse_verdict('{"ruling": "maybe", "rationale": "hmm"}')
    assert v.ruling == "revise"
    assert "unrecognised" in v.rationale
