"""Reporter snapshot result formatting.

Agent: reporter
Role: build typed snapshot presentation fields without graph traversal.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from contracts.common import Explanation

if TYPE_CHECKING:
    from collections.abc import Mapping
    from datetime import date


def snapshot_headline(
    portfolio: dict[str, float], signal: dict[str, float], performance_clause: str
) -> Explanation:
    """Return the operator-facing run headline."""
    return Explanation(
        summary=(
            f"{_count(portfolio, 'positions_opened')} positions opened; "
            f"{_count(portfolio, 'positions_closed')} closed; "
            f"{signal['recommendation_count']:.0f} recommendations stitched. "
            f"{performance_clause}"
        ),
        evidence_refs=("portfolio_manager", "execution", "monitor", "analyst"),
    )


def performance_headline_clause(
    metrics: Mapping[str, float], ticker: str | None, inception: date, reason: str
) -> str:
    """Return the benchmark-relative clause appended to the run headline."""
    if metrics["performance_sessions"] == 0.0:
        return f"Performance: no usable sessions since {inception} ({reason})"
    excess = _display_value(metrics["excess_return_pct"])
    exposure = _display_value(metrics["average_exposure_pct"])
    return (
        f"vs {ticker or 'benchmark'}: {excess:.2f} pts over "
        f"{metrics['performance_sessions']:.0f} sessions at {exposure:.0f}% invested"
    )


def _count(metrics: Mapping[str, float], key: str) -> str:
    # An undefined count is absent (RPT-NEV-03): `?`, never a zero it cannot be.
    value = metrics.get(key)
    return "?" if value is None else f"{value:.0f}"


def _display_value(value: float) -> float:
    return 0.0 if f"{value:.2f}" == "-0.00" else value
