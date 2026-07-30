"""Recommendation graph property serialization.

Agent: analyst
Role: convert typed analyst recommendation evidence into graph node properties.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from contracts.analyst import Recommendation, StopTargetEvidence


def recommendation_props(recommendation: Recommendation) -> dict[str, object]:
    """Return graph properties for a persisted Recommendation node."""
    props: dict[str, object] = {
        "ticker": recommendation.ticker,
        "action": recommendation.action,
        "exit_trigger": recommendation.exit_trigger,
        "confidence": recommendation.confidence,
        "technical_score": recommendation.technical_score,
        "suggested_stop_pct": recommendation.suggested_stop_pct,
        "suggested_target_pct": recommendation.suggested_target_pct,
        "quant_metrics": [
            metric.model_dump(mode="json") for metric in recommendation.quant_metrics
        ],
    }
    evidence = recommendation.stop_target_evidence
    if evidence is not None:
        props.update(_stop_target_props(evidence))
    return props


def _stop_target_props(evidence: StopTargetEvidence) -> dict[str, object]:
    return {
        "stop_target_mode": evidence.mode,
        "stop_target_counterfactual_mode": evidence.counterfactual_mode,
        "stop_target_atr_pct": evidence.atr_pct,
        "stop_target_volatility_present": evidence.volatility_present,
        "stop_target_volatility_fallback": evidence.volatility_fallback,
        "stop_target_applied_stop_pct": evidence.applied_stop_pct,
        "stop_target_applied_target_pct": evidence.applied_target_pct,
        "stop_target_counterfactual_stop_pct": evidence.counterfactual_stop_pct,
        "stop_target_counterfactual_target_pct": evidence.counterfactual_target_pct,
        "stop_target_flat_stop_pct": evidence.flat_stop_pct,
        "stop_target_flat_target_pct": evidence.flat_target_pct,
        "stop_target_scaled_stop_pct": evidence.scaled_stop_pct,
        "stop_target_scaled_target_pct": evidence.scaled_target_pct,
    }
