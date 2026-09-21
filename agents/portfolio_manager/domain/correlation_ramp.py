"""Correlation contribution ramp for Portfolio Manager concentration checks.

Agent: portfolio_manager
Role: map a measured issuer correlation to its bounded cluster contribution.
External I/O: none.
"""

from __future__ import annotations

from decimal import Decimal

_WEIGHT_PLACES = Decimal("0.0001")


def contribution(correlation: float | None, *, floor: float, ceiling: float) -> float:
    """Return the bounded contribution for one measured correlation."""
    if correlation is None:
        return 0.0
    if ceiling <= floor:
        return 1.0 if correlation >= floor else 0.0
    if correlation <= floor:
        return 0.0
    if correlation >= ceiling:
        return 1.0
    return float(
        (Decimal(str(correlation)) - Decimal(str(floor)))
        / (Decimal(str(ceiling)) - Decimal(str(floor)))
    )


def rounded_contribution(
    correlation: float | None, *, floor: float, ceiling: float
) -> float:
    """Return a contribution rounded once for both display and arithmetic."""
    return float(
        Decimal(str(contribution(correlation, floor=floor, ceiling=ceiling))).quantize(
            _WEIGHT_PLACES
        )
    )
