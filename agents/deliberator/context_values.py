"""Shared value formatting for deliberation evidence.

Agent: deliberator
Role: render packet numbers with explicit unit/scope labels where this agent owns
      the label, and with an honest source-owned boundary where it does not.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

    from contracts.analyst import Recommendation
    from contracts.common import Explanation

SOURCE_VALUE_BOUNDARY = (
    "Source-owned metric dictionaries: keys keep producer/vendor names; "
    "units/scope are unknown unless the key names them."
)

_GATE_VALUE_LABELS = {
    "sizing": ("value_portfolio_ratio", "threshold_portfolio_ratio"),
    "min_order_quantity": ("value_shares", "threshold_shares"),
    "max_positions": ("value_positions", "threshold_positions"),
    "cash_available": ("value_order_cost_usd", "threshold_available_cash_usd"),
    "reward_risk": ("value_reward_risk_ratio", "threshold_reward_risk_ratio"),
    "max_sector_pct": ("value_batch_sector_ratio", "threshold_sector_ratio"),
    "max_names_per_sector": ("value_sector_names", "threshold_sector_names"),
}


def gate_value_labels(name: str) -> tuple[str, str]:
    """Return unit/scope-aware labels for a generic gate value pair."""
    return _GATE_VALUE_LABELS.get(
        name, ("value_units_scope_unknown", "threshold_units_scope_unknown")
    )


def explain(value: Explanation) -> str:
    """Render an explanation summary with its evidence refs when present."""
    refs = f" refs={list(value.evidence_refs)}" if value.evidence_refs else ""
    return f"{value.summary}{refs}"


def number(value: float | None) -> str:
    """Render a dimensionless numeric score."""
    return "n/a" if value is None else f"{value:.3f}"


def percent(value: float | None) -> str:
    """Render a ratio as a percentage."""
    return "n/a" if value is None else f"{value:.2%}"


def quant_metrics(rec: Recommendation) -> str:
    """Render analyst-owned quant metrics without inventing missing units."""
    if not rec.quant_metrics:
        return "{}"
    return _source_owned_map(
        (metric.name, metric.value) for metric in rec.quant_metrics
    )


def source_metric_map(values: dict[str, float]) -> str:
    """Render an open-name value map with an explicit source-owned boundary."""
    return _source_owned_map((key, values[key]) for key in sorted(values))


def _source_owned_map(entries: Iterable[tuple[str, float]]) -> str:
    body = ", ".join(f"{key}={value:.4g}" for key, value in entries)
    return f"source-owned-units-scope-unknown{{{body}}}"
