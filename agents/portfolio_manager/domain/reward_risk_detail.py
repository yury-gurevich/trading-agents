"""Reward-risk gate detail rendering for Portfolio Manager.

Agent: portfolio_manager
Role: disclose whether the reward-risk comparison could have produced a
      different verdict from the evidence it had.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from contracts.analyst import Recommendation

_FLOAT_TOLERANCE = 1e-12


def reward_risk_detail(
    item: Recommendation,
    *,
    stop_pct: float,
    target_pct: float,
    default_stop_pct: float,
    default_target_pct: float,
) -> str:
    """Render the reward-risk gate's verdict-reachability disclosure."""
    comparison = _comparison_kind(
        item, stop_pct, target_pct, default_stop_pct, default_target_pct
    )
    return "; ".join(
        (
            f"target_pct={target_pct:.4f}",
            f"stop_pct={stop_pct:.4f}",
            f"base_take_profit_pct={default_target_pct:.4f}",
            f"base_stop_loss_pct={default_stop_pct:.4f}",
            f"source={_stop_target_source(item)}",
            f"applied_mode={_applied_mode(item)}",
            f"structural_basis={_structural_basis(item)}",
            f"target_basis={_target_basis(item)}",
            f"favorable_excursion_pct={_favorable_excursion_pct(item)}",
            f"favorable_excursion_horizon_days={_favorable_excursion_horizon_days(item)}",
            f"favorable_excursion_sample_count={_favorable_excursion_sample_count(item)}",
            f"comparison={comparison}",
        )
    )


def _stop_target_source(item: Recommendation) -> str:
    if item.suggested_stop_pct is not None or item.suggested_target_pct is not None:
        return "recommendation"
    return "regime"


def _applied_mode(item: Recommendation) -> str:
    evidence = item.stop_target_evidence
    if evidence is not None:
        return evidence.mode
    return _stop_target_source(item)


def _structural_basis(item: Recommendation) -> str:
    if item.stop_target_evidence is not None:
        return "base_take_profit_pct/base_stop_loss_pct"
    if item.suggested_stop_pct is None and item.suggested_target_pct is None:
        return "base_take_profit_pct/base_stop_loss_pct"
    return "recommendation_stop_pct/recommendation_target_pct"


def _target_basis(item: Recommendation) -> str:
    evidence = item.stop_target_evidence
    if evidence is not None and evidence.favorable_excursion_sample_count is not None:
        return "trailing_favorable_excursion"
    return _structural_basis(item)


def _favorable_excursion_pct(item: Recommendation) -> str:
    evidence = item.stop_target_evidence
    value = None if evidence is None else evidence.favorable_excursion_pct
    return "n/a" if value is None else f"{value:.4f}"


def _favorable_excursion_horizon_days(item: Recommendation) -> str:
    evidence = item.stop_target_evidence
    value = None if evidence is None else evidence.favorable_excursion_horizon_days
    return "n/a" if value is None else str(value)


def _favorable_excursion_sample_count(item: Recommendation) -> str:
    evidence = item.stop_target_evidence
    value = None if evidence is None else evidence.favorable_excursion_sample_count
    return "n/a" if value is None else str(value)


def _comparison_kind(
    item: Recommendation,
    stop_pct: float,
    target_pct: float,
    default_stop_pct: float,
    default_target_pct: float,
) -> str:
    if _is_structurally_determined(
        item, stop_pct, target_pct, default_stop_pct, default_target_pct
    ):
        return "STRUCTURALLY_DETERMINED"
    return "INFORMATIVE"


def _is_structurally_determined(
    item: Recommendation,
    stop_pct: float,
    target_pct: float,
    default_stop_pct: float,
    default_target_pct: float,
) -> bool:
    evidence = item.stop_target_evidence
    if evidence is None:
        return item.suggested_stop_pct is None and item.suggested_target_pct is None
    if evidence.favorable_excursion_sample_count is not None:
        return False
    return (
        _close(evidence.flat_stop_pct, default_stop_pct)
        and _close(evidence.flat_target_pct, default_target_pct)
        and _close(evidence.applied_stop_pct, stop_pct)
        and _close(evidence.applied_target_pct, target_pct)
        and _same_ratio(target_pct, stop_pct, default_target_pct, default_stop_pct)
    )


def _same_ratio(
    left_target: float,
    left_stop: float,
    right_target: float,
    right_stop: float,
) -> bool:
    if left_stop <= 0.0 or right_stop <= 0.0:
        return False
    return _close(left_target / left_stop, right_target / right_stop)


def _close(left: float, right: float) -> bool:
    return abs(left - right) <= _FLOAT_TOLERANCE
