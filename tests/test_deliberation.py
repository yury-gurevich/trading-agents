"""Deliberation harness tests — defend/attack/judge debate over a proposition.

Agent: kernel
Role: verify the bounded three-role debate produces a structured transcript and
      a parsed verdict, and that the Judge parser degrades safely.
External I/O: none.
"""

from __future__ import annotations

from kernel import Proposition, deliberate
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
