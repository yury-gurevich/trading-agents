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
    from contracts.deliberator import DebateTurnRecord

FAIL_OPEN_RATIONALE = "llm unavailable (fail-open)"


@dataclass(frozen=True)
class OrderReview:
    """One order's recorded debate outcome."""

    verdict: str
    rationale: str
    turns: tuple[DebateTurnRecord, ...]
    llm_call_keys: tuple[str, ...]
    failed_open: bool = False


def fail_open_review() -> OrderReview:
    """Return the lawful fail-open review marker for one affected order."""
    return OrderReview("uphold", FAIL_OPEN_RATIONALE, (), (), failed_open=True)


def debate_record(review: OrderReview) -> dict[str, object]:
    """Return the per-ticker debate payload stored on DeliberationRun."""
    return {
        "verdict": review.verdict,
        "rationale": review.rationale,
        "failed_open": review.failed_open,
        "turns": [
            {"role": turn.role, "round": turn.round, "text": turn.text}
            for turn in review.turns
        ],
    }


def transcript_records(
    ticker: str, turns: tuple[DebateTurnRecord, ...]
) -> list[dict[str, object]]:
    """Return transcript rows stamped with the order ticker."""
    return [
        {"ticker": ticker, "role": turn.role, "round": turn.round, "text": turn.text}
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
    """Return the three models stamped on a DeliberationRun."""
    return {
        "defender": settings.defender_model,
        "challenger": settings.challenger_model,
        "judge": settings.judge_model,
    }
