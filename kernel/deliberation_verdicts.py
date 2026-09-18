"""Deliberation judge verdict parsing.

Agent: kernel
Role: parse bounded judge rulings without choosing trading policy.
External I/O: none directly.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

_RULINGS = ("uphold", "overturn", "revise")


class UnreadableVerdictError(ValueError):
    """Raised when a judge answer cannot be treated as a verdict."""


@dataclass(frozen=True)
class Verdict:
    """The Judge's ruling on the proposition."""

    ruling: str
    rationale: str


def parse_verdict(raw: str) -> Verdict:
    """Parse the Judge's JSON, raising when no ruling can be read."""
    if not raw.strip():
        raise UnreadableVerdictError("judge response empty")
    try:
        data = json.loads(raw)
        ruling = str(data["ruling"]).strip().lower()
        rationale = str(data.get("rationale", "")).strip()
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        raise UnreadableVerdictError("judge response unparseable") from exc
    if ruling not in _RULINGS:
        raise UnreadableVerdictError(f"unrecognised ruling {ruling!r}")
    return Verdict(ruling, rationale)
