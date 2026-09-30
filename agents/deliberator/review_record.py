"""Deliberator review record helpers.

Agent: deliberator
Role: shape per-order debate outcomes into durable DeliberationRun fields.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agents.deliberator.settings import DeliberatorSettings
    from contracts.deliberator import DebateProposition, DebateTurnRecord

_FAILED_OPEN_REASON_LIMIT = 500
_UNKNOWN_FAIL_OPEN_REASON = "UnknownError: reason unavailable"


@dataclass(frozen=True)
class OrderReview:
    """One order's recorded debate outcome."""

    verdict: str
    rationale: str
    turns: tuple[DebateTurnRecord, ...]
    llm_call_keys: tuple[str, ...]
    failed_open: bool = False
    failed_open_reason: str = ""
    #: The packet the roles were given; None only when building it failed.
    proposition: DebateProposition | None = None


def failed_open_reason(error_type: str, message: str) -> str:
    """Return the queryable fail-open cause stamped on DeliberationRun."""
    reason = f"{error_type}: {message}"
    if len(reason) <= _FAILED_OPEN_REASON_LIMIT:
        return reason
    return reason[: _FAILED_OPEN_REASON_LIMIT - 3] + "..."


def fail_open_review(
    reason: str | None = None, proposition: DebateProposition | None = None
) -> OrderReview:
    """Return the lawful fail-open review marker for one affected order."""
    recorded_reason = reason or _UNKNOWN_FAIL_OPEN_REASON
    return OrderReview(
        "uphold",
        f"fail-open: {recorded_reason}",
        (),
        (),
        failed_open=True,
        failed_open_reason=recorded_reason,
        proposition=proposition,
    )


def debate_record(review: OrderReview) -> dict[str, object]:
    """Return the per-ticker debate payload stored on DeliberationRun.

    The decision and packet are stored once per order, since every turn of the
    order read the same one (DLIB-OUT-07, DL-252 D4).
    """
    proposition = review.proposition
    return {
        "verdict": review.verdict,
        "rationale": review.rationale,
        "failed_open": review.failed_open,
        "failed_open_reason": review.failed_open_reason,
        "turns": [
            {"role": turn.role, "round": turn.round, "text": turn.text}
            for turn in review.turns
        ],
        "decision": proposition.decision if proposition is not None else None,
        "context": proposition.context if proposition is not None else None,
    }


def transcript_records(
    ticker: str, turns: tuple[DebateTurnRecord, ...]
) -> list[dict[str, object]]:
    """Return transcript rows stamped with the order ticker (DLIB-OUT-06).

    Each row keeps the guided reasoning exactly as parsed, or why it could not
    be read; a turn recorded before S246 has neither and reads as ``None``.
    """
    return [
        {
            "ticker": ticker,
            "role": turn.role,
            "round": turn.round,
            "text": turn.text,
            "reasoning": (
                turn.reasoning.model_dump(mode="json")
                if turn.reasoning is not None
                else None
            ),
            "reasoning_error": turn.reasoning_error,
        }
        for turn in turns
    ]


def narrative(debates: dict[str, object]) -> str:
    """Render the human-readable deliberation summary."""
    if not debates:
        return "No PM-approved orders required deliberation."
    return "; ".join(
        f"{ticker}: {record['verdict']} - {record['rationale']}"
        for ticker, record in sorted(debates.items())
        if isinstance(record, dict)
    )


def role_models(settings: DeliberatorSettings) -> dict[str, str]:
    """Return the three *resolved* models stamped on a DeliberationRun.

    Reads through `model_for_role` rather than the tunables, so the audit record
    names the model that actually answered — never the empty sentinel, and never
    the other vendor's name after a provider switch (DL-100).
    """
    return {
        "defender": settings.model_for_role("defender"),
        "challenger": settings.model_for_role("challenger"),
        "judge": settings.model_for_role("judge"),
    }
