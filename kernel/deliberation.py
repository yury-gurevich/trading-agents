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
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kernel.llm import LLMClient

_RULINGS = ("uphold", "overturn", "revise")

DEFENDER_SYSTEM = (
    "You are the DEFENDER in a decision review. Argue *for* the decision with "
    "the strongest, most honest case. Be concrete; cite the evidence. 3 sentences max."
)
CHALLENGER_SYSTEM = (
    "You are the CHALLENGER in a decision review. Attack the decision: find its "
    "weakest assumptions, risks, and failure modes. Do not be polite or hedge. "
    "If it is genuinely sound, give the single strongest objection. 3 sentences max."
)
JUDGE_SYSTEM = (
    "You are the JUDGE in a decision review. Weigh the Defender vs the Challenger "
    "on the merits, not the volume. Reply ONLY as JSON: "
    '{"ruling": "uphold|overturn|revise", "rationale": "<one line>"}.'
)
_ROUND_ROLES = (("defender", DEFENDER_SYSTEM), ("challenger", CHALLENGER_SYSTEM))


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


def _render(proposition: Proposition, transcript: tuple[Turn, ...]) -> str:
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
    try:
        data = json.loads(raw)
        ruling = str(data["ruling"]).strip().lower()
        rationale = str(data.get("rationale", "")).strip()
    except (json.JSONDecodeError, KeyError, TypeError):
        return Verdict("revise", "judge response unparseable — defaulting to revise")
    if ruling not in _RULINGS:
        return Verdict("revise", f"unrecognised ruling {ruling!r}; defaulted to revise")
    return Verdict(ruling, rationale)


def deliberate(
    llm: LLMClient, proposition: Proposition, *, max_rounds: int = 3
) -> DebateResult:
    """Run the bounded debate and return the transcript + verdict.

    Each round: the Defender argues, then the Challenger rebuts, each seeing the
    proposition and the running transcript. After ``max_rounds`` the Judge rules.
    ``max_rounds`` is clamped to at least 1 — a debate is bounded, never empty.
    """
    rounds = max(1, max_rounds)
    transcript: list[Turn] = []
    for r in range(1, rounds + 1):
        for role, system in _ROUND_ROLES:
            text = llm.complete(
                system=system,
                user=_render(proposition, tuple(transcript)),
                tool_schema={},
            ).strip()
            transcript.append(Turn(role, r, text))
    raw = llm.complete(
        system=JUDGE_SYSTEM,
        user=_render(proposition, tuple(transcript)),
        tool_schema={},
    )
    return DebateResult(proposition, tuple(transcript), _parse_verdict(raw))
