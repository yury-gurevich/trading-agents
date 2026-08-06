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
    directional_n: int
    hit_rate: float | None
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
    grouped: dict[str, list[tuple[str, float]]] = {}
    for outcome in outcomes:
        bucket = bucket_for(outcome)
        assert outcome.forward_return is not None
        grouped.setdefault(bucket, []).append((outcome.action, outcome.forward_return))
    return [
        _score(horizon, cut, bucket, items) for bucket, items in sorted(grouped.items())
    ]


def _is_hit(action: str, forward_return: float) -> bool:
    """Was the directional call right? A sell is right when the price FALLS."""
    return forward_return < 0.0 if action == "sell" else forward_return > 0.0


def _score(
    horizon: int, cut: str, bucket: str, items: list[tuple[str, float]]
) -> ScoreRow:
    """Score one bucket, counting hits only for directional recommendations.

    `hold` is not a directional call, so it cannot be hit or missed and is
    excluded from `hit_rate` while still contributing to the return statistics.
    Scoring every row as `forward_return > 0` inverted every `sell`: the first
    live scorecard reported 1-day sells at a 16.67% hit rate on a -6.75% mean
    return (the sells were right) and 5-day sells at 80% on +6.17% (they were
    wrong).
    """
    returns = [value for _action, value in items]
    directional = [(a, v) for a, v in items if a in ("buy", "sell")]
    return ScoreRow(
        horizon=horizon,
        cut=cut,
        bucket=bucket,
        n=len(returns),
        directional_n=len(directional),
        hit_rate=(
            sum(_is_hit(a, v) for a, v in directional) / len(directional)
            if directional
            else None
        ),
        mean_return=fmean(returns),
        median_return=median(returns),
    )


def _confidence_bucket(confidence: float, width: float) -> str:
    if width <= 0.0 or width > 1.0:
        raise ValueError("confidence bucket width must be in (0, 1]")
    decimal_width = Decimal(str(width))
    lower = (Decimal(str(confidence)) // decimal_width) * decimal_width
    return f"{lower:f}-{lower + decimal_width:f}"
