"""Stop-target basis renderer for deliberation evidence.

Agent: deliberator
Role: render analyst stop-target proposal evidence without inventing a gate.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.deliberator.context_values import percent

if TYPE_CHECKING:
    from contracts.analyst import Recommendation


def stop_target_basis(rec: Recommendation) -> str:
    """Render which stop mode ran and whether volatility evidence was available."""
    evidence = rec.stop_target_evidence
    if evidence is None:
        return "stop_target basis: unavailable"
    atr_pct = None if evidence.atr_pct is None else evidence.atr_pct / 100
    return (
        "stop_target basis: "
        f"mode={evidence.mode}; "
        f"volatility_present={evidence.volatility_present}; "
        f"volatility_fallback={evidence.volatility_fallback}; "
        f"atr_pct={percent(atr_pct)}; "
        f"applied_stop_pct={percent(evidence.applied_stop_pct)}; "
        f"applied_target_pct={percent(evidence.applied_target_pct)}; "
        f"counterfactual_mode={evidence.counterfactual_mode}"
    )
