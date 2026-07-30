"""Recommendation volatility passthrough helpers.

Agent: portfolio_manager
Role: copy analyst-emitted volatility onto OrderIntent without interpreting it.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from contracts.analyst import Recommendation

ATR_METRIC_NAME = "atr_pct"


def decision_atr_pct(item: Recommendation) -> float | None:
    """Return the analyst's ATR percent metric unchanged when present."""
    for metric in item.quant_metrics:
        if metric.name == ATR_METRIC_NAME:
            return metric.value
    return None
