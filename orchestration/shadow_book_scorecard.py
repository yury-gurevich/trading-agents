"""Score and render read-only recommendation outcomes.

Agent: orchestration
Role: aggregate the shadow book by action, confidence, and recorded disposition.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from statistics import fmean, median
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

    from orchestration.shadow_book import ShadowOutcome


@dataclass(frozen=True)
class ScoreRow:
    """One complete-case scorecard bucket."""

    horizon: int
    cut: str
    bucket: str
    n: int
    hit_rate: float
    mean_return: float
    median_return: float


def score_rows(
    outcomes: tuple[ShadowOutcome, ...], *, confidence_bucket_width: float
) -> tuple[ScoreRow, ...]:
    """Compute complete-case statistics for every required scorecard cut."""
    rows: list[ScoreRow] = []
    complete = [outcome for outcome in outcomes if outcome.status == "scored"]
    for horizon in sorted({outcome.horizon for outcome in outcomes}):
        horizon_rows = [item for item in complete if item.horizon == horizon]
        rows.extend(_group(horizon, "all", horizon_rows, lambda _item: "all"))
        rows.extend(
            _group(
                horizon,
                "disposition",
                horizon_rows,
                lambda item: item.disposition,
            )
        )
        rows.extend(_group(horizon, "action", horizon_rows, lambda item: item.action))
        rows.extend(
            _group(
                horizon,
                "confidence",
                horizon_rows,
                lambda item: _confidence_bucket(
                    item.confidence, confidence_bucket_width
                ),
            )
        )
    return tuple(rows)


def _group(
    horizon: int,
    cut: str,
    outcomes: list[ShadowOutcome],
    bucket_for: Callable[[ShadowOutcome], str],
) -> list[ScoreRow]:
    grouped: dict[str, list[float]] = {}
    for outcome in outcomes:
        bucket = bucket_for(outcome)
        assert outcome.forward_return is not None
        grouped.setdefault(bucket, []).append(outcome.forward_return)
    return [
        _score(horizon, cut, bucket, returns)
        for bucket, returns in sorted(grouped.items())
    ]


def _score(horizon: int, cut: str, bucket: str, returns: list[float]) -> ScoreRow:
    return ScoreRow(
        horizon=horizon,
        cut=cut,
        bucket=bucket,
        n=len(returns),
        hit_rate=sum(value > 0.0 for value in returns) / len(returns),
        mean_return=fmean(returns),
        median_return=median(returns),
    )


def _confidence_bucket(confidence: float, width: float) -> str:
    if width <= 0.0 or width > 1.0:
        raise ValueError("confidence bucket width must be in (0, 1]")
    decimal_width = Decimal(str(width))
    lower = (Decimal(str(confidence)) // decimal_width) * decimal_width
    return f"{lower:f}-{lower + decimal_width:f}"


def render_scorecard(
    outcomes: tuple[ShadowOutcome, ...],
    horizons: tuple[int, ...],
    *,
    confidence_bucket_width: float,
) -> str:
    """Render coverage and all required cuts with an explicit sample size."""
    recommendation_refs = {item.recommendation_ref for item in outcomes}
    reference_priced = {
        item.recommendation_ref for item in outcomes if item.reference_price is not None
    }
    scored = sum(item.status == "scored" for item in outcomes)
    unpriceable = sum(item.status == "unpriceable" for item in outcomes)
    not_elapsed = sum(item.status == "not_yet_elapsed" for item in outcomes)
    by_recommendation = {item.recommendation_ref: item for item in outcomes}
    disposition_counts = {
        disposition: sum(
            item.disposition == disposition for item in by_recommendation.values()
        )
        for disposition in (
            "taken",
            "blocked_capacity",
            "blocked_other",
            "not_actionable",
        )
    }
    lines = [
        "SHADOW BOOK SCORECARD",
        (
            f"recommendations_seen={len(recommendation_refs)} "
            f"reference_priced={len(reference_priced)} "
            f"reference_unpriceable={len(recommendation_refs - reference_priced)}"
        ),
        (
            f"outcomes_scored={scored} outcomes_unpriceable={unpriceable} "
            f"horizons_not_yet_elapsed={not_elapsed}"
        ),
        (
            f"dispositions taken={disposition_counts['taken']} "
            f"blocked_capacity={disposition_counts['blocked_capacity']} "
            f"blocked_other={disposition_counts['blocked_other']} "
            f"not_actionable={disposition_counts['not_actionable']}"
        ),
    ]
    rows = score_rows(outcomes, confidence_bucket_width=confidence_bucket_width)
    for horizon in horizons:
        horizon_outcomes = [item for item in outcomes if item.horizon == horizon]
        lines.extend(_render_horizon(horizon, horizon_outcomes, rows))
    return "\n".join(lines)


def _render_horizon(
    horizon: int,
    outcomes: list[ShadowOutcome],
    rows: tuple[ScoreRow, ...],
) -> list[str]:
    status_counts = {
        status: sum(item.status == status for item in outcomes)
        for status in ("scored", "unpriceable", "not_yet_elapsed")
    }
    lines = [
        "",
        f"HORIZON {horizon} TRADING DAYS",
        (
            f"coverage n={len(outcomes)} scored={status_counts['scored']} "
            f"unpriceable={status_counts['unpriceable']} "
            f"not_yet_elapsed={status_counts['not_yet_elapsed']}"
        ),
        "| cut | bucket | n | hit_rate | mean_return | median_return |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    horizon_rows = [row for row in rows if row.horizon == horizon]
    if not horizon_rows:
        lines.append("| all | no complete outcomes | 0 | N/A | N/A | N/A |")
    lines.extend(_render_row(row) for row in horizon_rows)
    return lines


def _render_row(row: ScoreRow) -> str:
    return (
        f"| {row.cut} | {row.bucket} | {row.n} | {row.hit_rate:.2%} | "
        f"{row.mean_return:.2%} | {row.median_return:.2%} |"
    )
