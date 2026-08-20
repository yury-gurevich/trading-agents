"""Reward-risk gate and approved-order construction for the Portfolio Manager.

Agent: portfolio_manager
Role: resolve stop/target percentages with their reward-risk evidence, and build
      the approved order carrying the gates that were evaluated.
External I/O: none.

Entry-sizing gates live in `position_gates`, so neither module approaches the
200-line hard block.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from agents.portfolio_manager.domain.volatility import decision_atr_pct
from contracts.common import Explanation
from contracts.portfolio_manager import (
    GateOutcome,
    GateStatus,
    OrderIntent,
    RejectedOrder,
)

if TYPE_CHECKING:
    from contracts.analyst import Recommendation
    from contracts.common import Money


@dataclass(frozen=True)
class StopTarget:
    """Resolved stop/target percentages plus their reward-risk gate outcome."""

    stop_pct: float
    target_pct: float
    outcome: GateOutcome


def stop_target_report(
    item: Recommendation,
    default_stop_pct: float,
    default_target_pct: float,
    min_ratio: float,
) -> StopTarget:
    """Resolve stop/target percentages and report the reward-risk gate."""
    stop_pct = (
        item.suggested_stop_pct
        if item.suggested_stop_pct is not None
        else default_stop_pct
    )
    target_pct = (
        item.suggested_target_pct
        if item.suggested_target_pct is not None
        else default_target_pct
    )
    ratio = 0.0 if stop_pct <= 0.0 else target_pct / stop_pct
    return StopTarget(
        stop_pct=stop_pct,
        target_pct=target_pct,
        outcome=GateOutcome(
            name="reward_risk",
            value=ratio,
            threshold=min_ratio,
            outcome=(
                GateStatus.PASSED
                if stop_pct > 0.0 and ratio >= min_ratio
                else GateStatus.FAILED
            ),
            detail=(
                f"target_pct={target_pct:.4f}; stop_pct={stop_pct:.4f}; "
                f"source={_stop_target_source(item)}"
            ),
        ),
    )


def reward_risk_rejection(
    ticker: str,
    report: StopTarget,
    prior_outcomes: tuple[GateOutcome, ...] = (),
) -> RejectedOrder | None:
    """Return the existing reward-risk rejection reason with evaluated gates."""
    gate_report = (*prior_outcomes, report.outcome)
    reason = None
    if report.stop_pct <= 0.0:
        reason = "invalid_stop_loss"
    elif report.outcome.outcome == GateStatus.FAILED:
        reason = "reward_risk_below_min"
    if reason is None:
        return None
    return RejectedOrder(ticker=ticker, reason=reason, gate_report=gate_report)


def order_intent(
    item: Recommendation,
    quantity: int,
    price: Money,
    report: StopTarget,
    outcomes: tuple[GateOutcome, ...],
) -> OrderIntent:
    """Build the approved order with its additive PM gate report."""
    return OrderIntent(
        ticker=item.ticker,
        action=item.action,
        quantity=quantity,
        est_price=price,
        decision_atr_pct=decision_atr_pct(item),
        stop_pct=report.stop_pct,
        target_pct=report.target_pct,
        rationale=Explanation(
            summary=f"Approved {item.ticker}: sized {quantity} shares from PM policy.",
            evidence_refs=("portfolio_manager.sizing", "provider.regime"),
        ),
        gate_report=outcomes,
    )


def _stop_target_source(item: Recommendation) -> str:
    return "recommendation" if item.suggested_stop_pct is not None else "regime"
