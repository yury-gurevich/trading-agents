"""Shadow-book scorecard rendering.

Agent: orchestration
Role: render shadow-book coverage and score rows as an operator-readable table.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from orchestration.shadow_book_scorecard import ScoreRow, score_rows

if TYPE_CHECKING:
    from orchestration.shadow_book import ShadowOutcome


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
        "| cut | bucket | n | dir_n | hit_rate | mean_return | median_return |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    horizon_rows = [row for row in rows if row.horizon == horizon]
    if not horizon_rows:
        lines.append("| all | no complete outcomes | 0 | 0 | n/a | n/a | n/a |")
    lines.extend(_render_row(row) for row in horizon_rows)
    return lines


def _render_row(row: ScoreRow) -> str:
    return (
        f"| {row.cut} | {row.bucket} | {row.n} | {row.directional_n} | "
        f"{'n/a' if row.hit_rate is None else format(row.hit_rate, '.2%')} | "
        f"{row.mean_return:.2%} | {row.median_return:.2%} |"
    )
