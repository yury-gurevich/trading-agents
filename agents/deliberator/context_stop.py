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
    from contracts.portfolio_manager import OrderIntent
    from contracts.provider import RegimeContext


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


def stop_regime_basis(
    regime: RegimeContext | None, rec: Recommendation | None, intent: OrderIntent
) -> str:
    """Render regime-related stop evidence as descriptive basis, not a verdict."""
    if regime is None:
        return (
            "stop_target_regime basis: unavailable: no regime context; "
            f"stop_pct={percent(intent.stop_pct)}; "
            f"target_pct={percent(intent.target_pct)}."
        )
    if rec is None or rec.stop_target_evidence is None:
        return (
            "stop_target_regime basis: unavailable: no analyst stop-target evidence; "
            f"stop_pct={percent(intent.stop_pct)}; "
            f"target_pct={percent(intent.target_pct)}; "
            f"base_stop_loss_pct={percent(regime.base_stop_loss_pct)}; "
            f"base_take_profit_pct={percent(regime.base_take_profit_pct)}."
        )
    evidence = rec.stop_target_evidence
    applied_ratio = _reward_risk_ratio(
        evidence.applied_target_pct, evidence.applied_stop_pct
    )
    flat_ratio = _reward_risk_ratio(evidence.flat_target_pct, evidence.flat_stop_pct)
    scaled_ratio = _reward_risk_ratio(
        evidence.scaled_target_pct, evidence.scaled_stop_pct
    )
    return (
        "stop_target_regime basis: "
        f"mode={evidence.mode}; "
        f"applied_stop_pct={percent(evidence.applied_stop_pct)}; "
        f"applied_target_pct={percent(evidence.applied_target_pct)}; "
        f"flat_stop_pct={percent(evidence.flat_stop_pct)}; "
        f"flat_target_pct={percent(evidence.flat_target_pct)}; "
        f"scaled_stop_pct={percent(evidence.scaled_stop_pct)}; "
        f"scaled_target_pct={percent(evidence.scaled_target_pct)}; "
        f"counterfactual_mode={evidence.counterfactual_mode}; "
        f"applied_reward_risk_ratio={applied_ratio}; "
        f"flat_reward_risk_ratio={flat_ratio}; "
        f"scaled_reward_risk_ratio={scaled_ratio}"
    )


def _reward_risk_ratio(target_pct: float, stop_pct: float) -> str:
    if stop_pct <= 0.0:
        return "n/a"
    return f"{target_pct / stop_pct:.2f}"
