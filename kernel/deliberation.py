"""Deliberation harness — defend / attack / judge a decision via LLM debate.

Agent: kernel
Role: run a bounded three-role LLM debate (Defender argues for, Challenger
      attacks, Judge rules) over a proposition and return the transcript + a
      verdict — the recorded LAW-05 "why". Stress-tests a decision; never makes
      or executes one. Governed by ops/departments/deliberation/charter.md.
External I/O: none directly (the model is reached via the injected LLMClient).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from kernel.deliberation_prompts import (
    CHALLENGER_SYSTEM as CHALLENGER_SYSTEM,
)
from kernel.deliberation_prompts import (
    DEFENDER_SYSTEM as DEFENDER_SYSTEM,
)
from kernel.deliberation_prompts import (
    JUDGE_SYSTEM as JUDGE_SYSTEM,
)
from kernel.llm import LLMCompletionStoppedError

if TYPE_CHECKING:
    from kernel.llm import LLMClient

_RULINGS = ("uphold", "overturn", "revise")
DebateRole = Literal["defender", "challenger"]


@dataclass(frozen=True)
class DeliberationPrompts:
    """The system prompts used by each deliberation role."""

    defender: str
    challenger: str
    judge: str

    def round_roles(self) -> tuple[tuple[DebateRole, str], ...]:
        """Return the speaking roles for one debate round."""
        return (("defender", self.defender), ("challenger", self.challenger))


DEFAULT_DELIBERATION_PROMPTS = DeliberationPrompts(
    defender=DEFENDER_SYSTEM,
    challenger=CHALLENGER_SYSTEM,
    judge=JUDGE_SYSTEM,
)


@dataclass(frozen=True)
class Proposition:
    """The decision under test plus the evidence/context the roles reason over."""

    decision: str
    context: str


@dataclass(frozen=True)
class Turn:
    """One role's contribution in one round of the debate."""

    role: str
    round: int
    text: str


@dataclass(frozen=True)
class Verdict:
    """The Judge's ruling on the proposition."""

    ruling: str
    rationale: str


@dataclass(frozen=True)
class DebateResult:
    """The full record: the proposition, the transcript, and the verdict."""

    proposition: Proposition
    transcript: tuple[Turn, ...]
    verdict: Verdict


def render_debate_prompt(proposition: Proposition, transcript: tuple[Turn, ...]) -> str:
    """Build the shared user context: the proposition + the debate so far."""
    lines = [
        f"DECISION UNDER TEST: {proposition.decision}",
        f"CONTEXT / EVIDENCE: {proposition.context}",
        "",
        "DEBATE SO FAR:",
    ]
    lines.extend(f"  [{t.role} r{t.round}] {t.text}" for t in transcript)
    if not transcript:
        lines.append("  (none yet)")
    return "\n".join(lines)


def _parse_verdict(raw: str) -> Verdict:
    """Parse the Judge's JSON; fall back to 'revise' when it is unreadable."""
    if not raw.strip():
        return Verdict("revise", "judge response empty — defaulting to revise")
    try:
        data = json.loads(raw)
        ruling = str(data["ruling"]).strip().lower()
        rationale = str(data.get("rationale", "")).strip()
    except (json.JSONDecodeError, KeyError, TypeError):
        return Verdict("revise", "judge response unparseable — defaulting to revise")
    if ruling not in _RULINGS:
        return Verdict("revise", f"unrecognised ruling {ruling!r}; defaulted to revise")
    return Verdict(ruling, rationale)


def debate_turn(
    llm: LLMClient,
    proposition: Proposition,
    *,
    role: DebateRole,
    round_number: int,
    transcript: tuple[Turn, ...],
    prompts: DeliberationPrompts = DEFAULT_DELIBERATION_PROMPTS,
) -> Turn:
    """Ask one arguing role for its next turn using the shared prompt context."""
    system = prompts.defender if role == "defender" else prompts.challenger
    text = llm.complete(
        system=system,
        user=render_debate_prompt(proposition, transcript),
        tool_schema={},
    ).strip()
    if not text:
        raise LLMCompletionStoppedError(
            provider="kernel", stop_reason="empty_debate_turn"
        )
    return Turn(role, round_number, text)


def judge_verdict(
    llm: LLMClient,
    proposition: Proposition,
    *,
    transcript: tuple[Turn, ...],
    prompts: DeliberationPrompts = DEFAULT_DELIBERATION_PROMPTS,
) -> Verdict:
    """Ask the debate Judge to rule using the same parser as ``deliberate``."""
    try:
        raw = llm.complete(
            system=prompts.judge,
            user=render_debate_prompt(proposition, transcript),
            tool_schema={},
        )
    except LLMCompletionStoppedError as exc:
        return Verdict("revise", f"judge response stopped: {exc}")
    return _parse_verdict(raw)


def deliberate(
    llm: LLMClient,
    proposition: Proposition,
    *,
    max_rounds: int = 3,
    judge_llm: LLMClient | None = None,
    prompts: DeliberationPrompts = DEFAULT_DELIBERATION_PROMPTS,
) -> DebateResult:
    """Run the bounded debate and return the transcript + verdict.

    Each round: the Defender argues, then the Challenger rebuts, each seeing the
    proposition and the running transcript. After ``max_rounds`` the Judge rules.
    ``judge_llm`` optionally separates that final debate Judge from the arguing
    model. ``prompts`` can override one or more role prompts; the default value is
    the hand-written champion prompts, byte-for-byte. ``max_rounds`` is clamped to
    at least 1 — a debate is bounded, never empty.
    """
    rounds = max(1, max_rounds)
    transcript: list[Turn] = []
    for r in range(1, rounds + 1):
        for role, _system in prompts.round_roles():
            transcript.append(
                debate_turn(
                    llm,
                    proposition,
                    role=role,
                    round_number=r,
                    transcript=tuple(transcript),
                    prompts=prompts,
                )
            )
    ruling_llm = judge_llm if judge_llm is not None else llm
    return DebateResult(
        proposition,
        tuple(transcript),
        judge_verdict(
            ruling_llm, proposition, transcript=tuple(transcript), prompts=prompts
        ),
    )
