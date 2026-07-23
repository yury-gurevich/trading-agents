"""Portfolio Manager exit-order helpers.

Agent: portfolio_manager
Role: size full exits and report PM gates for sell recommendations.
External I/O: none.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from contracts.common import Explanation
from contracts.portfolio_manager import GateOutcome, OrderIntent

if TYPE_CHECKING:
    from agents.portfolio_manager.portfolio import PortfolioState
    from contracts.analyst import Recommendation
    from contracts.common import Money


def exit_outcomes(
    *,
    item: Recommendation,
    quantity: int,
    price: Money,
    portfolio: PortfolioState,
    min_order_quantity: int,
    max_positions: int,
) -> tuple[GateOutcome, ...]:
    """Report the same position gates for a full-exit sell."""
    value = Decimal(quantity) * price.amount
    open_after = max(0, len(portfolio.positions) - 1)
    return (
        GateOutcome(
            name="sizing",
            value=float(value / portfolio.value) if portfolio.value > 0 else 0.0,
            threshold=1.0,
            passed=True,
            detail=f"full_exit_quantity={quantity}; exit_value={value:.2f}",
        ),
        GateOutcome(
            name="min_order_quantity",
            value=float(quantity),
            threshold=float(min_order_quantity),
            passed=quantity >= min_order_quantity,
            detail=f"whole-share exit quantity for {item.ticker}",
        ),
        GateOutcome(
            name="max_positions",
            value=float(open_after),
            threshold=float(max_positions),
            passed=True,
            detail="sell reduces open position count",
        ),
        GateOutcome(
            name="cash_available",
            value=0.0,
            threshold=float(portfolio.cash.amount),
            passed=True,
            detail="sell raises cash; no buying-power draw",
        ),
    )


def exit_order_intent(
    item: Recommendation,
    quantity: int,
    price: Money,
    outcomes: tuple[GateOutcome, ...],
    position_ref: str | None,
) -> OrderIntent:
    """Build a full-exit sell OrderIntent on the existing execution rail."""
    return OrderIntent(
        ticker=item.ticker,
        action="sell",
        quantity=quantity,
        est_price=price,
        position_ref=position_ref,
        rationale=Explanation(
            summary=f"Approved {item.ticker}: full exit of {quantity} held shares.",
            evidence_refs=("portfolio_manager.sizing", "analyst.technical_score"),
        ),
        gate_report=outcomes,
    )
