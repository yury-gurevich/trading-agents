"""Say when a tolerance comparison could not have come out any other way.

Agent: tooling
Role: classify whether the flat-vs-scaled comparison was able to discriminate.
External I/O: none.

🚨 The comparison's denominator is *filled* orders, and an order only fills if
the applied band accepted it. So the applied mode's drop rate is 0.00 by
construction, and the counterfactual mode can only drop a row where its band is
the **narrower** one. When the applied band is narrower everywhere — flat at a
fixed 50 bps against scaled's 75-250 on 170 of 170 rows, measured 2026-09-13 —
both columns read 0.00 and no other answer was reachable.

🎯 That is the state [DL-165] flipped: since the operator promoted `scaled`, the
applied band is the wider one, so a fill above the flat limit is exactly an order
flat would have refused, and the report starts discriminating on its own.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ToleranceRow:
    """One filled order's applied mode and both candidate limits."""

    applied_mode: str | None
    side: str
    flat_limit_cents: int
    scaled_limit_cents: int


@dataclass(frozen=True)
class Informativeness:
    """How many rows were able to separate the two modes."""

    rows: int
    discriminating: int
    unclassified: int

    @property
    def forced(self) -> bool:
        """True when no row could have produced a non-zero counterfactual drop."""
        return self.rows > 0 and self.discriminating == 0


def assess(rows: tuple[ToleranceRow, ...]) -> Informativeness:
    """Count rows whose applied band was wider than the counterfactual band."""
    discriminating = sum(1 for row in rows if _applied_band_is_wider(row) is True)
    unclassified = sum(1 for row in rows if _applied_band_is_wider(row) is None)
    return Informativeness(
        rows=len(rows), discriminating=discriminating, unclassified=unclassified
    )


def render_comparison_line(info: Informativeness) -> str:
    """Render the labelled line that says whether the answer was forced."""
    if info.rows == 0:
        return "comparison: NO DATA - no eligible orders carry tolerance evidence"
    if info.forced:
        body = (
            f"comparison: FORCED - the applied band was never the wider one on any "
            f"of {info.rows} rows, so neither mode could have shown a drop"
        )
    else:
        body = (
            f"comparison: INFORMATIVE - the applied band was the wider one on "
            f"{info.discriminating} of {info.rows} rows, where a drop is observable"
        )
    if info.unclassified:
        body += f" ({info.unclassified} rows record no applied mode and were skipped)"
    return body


def _applied_band_is_wider(row: ToleranceRow) -> bool | None:
    """Return None when the row does not say which band was actually applied."""
    if row.applied_mode == "flat":
        applied, counterfactual = row.flat_limit_cents, row.scaled_limit_cents
    elif row.applied_mode == "scaled":
        applied, counterfactual = row.scaled_limit_cents, row.flat_limit_cents
    else:
        return None
    if row.side == "buy":
        return applied > counterfactual
    return applied < counterfactual
