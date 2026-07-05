"""Gate-outcome report helpers for Portfolio Manager risk checks.

Agent: portfolio_manager
Role: capture explicit pass/fail evidence for approved order risk gates.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING

from contracts.common import Explanation, Money
from contracts.portfolio_manager import GateOutcome, OrderIntent, RejectedOrder

if TYPE_CHECKING:
    from agents.portfolio_manager.portfolio import PortfolioState
    from contracts.analyst import Recommendation


@dataclass(frozen=True)
class StopTarget:
    """Resolved stop/target percentages plus their reward-risk gate outcome."""

    stop_pct: float
    target_pct: float
    outcome: GateOutcome


def position_outcomes(
    *,
    item: Recommendation,
    quantity: int,
    price: Money,
    portfolio: PortfolioState,
    reserved_cash: Decimal,
    open_tickers: set[str],
    max_position_pct: Decimal,
    max_positions: int,
    cash_buffer_pct: Decimal,
    min_order_quantity: int,
) -> tuple[GateOutcome, ...]:
    """Report the PM sizing, quantity, name-count, and cash gates."""
    cost = Decimal(quantity) * price.amount
    available = portfolio.cash.amount * (Decimal("1") - cash_buffer_pct) - reserved_cash
    is_new = item.ticker not in open_tickers
    open_after = len(open_tickers) + int(is_new)
    return (
        GateOutcome(
            name="sizing",
            value=_ratio(cost, portfolio.value),
            threshold=float(max_position_pct),
            passed=cost <= max_position_pct * portfolio.value,
            detail=(
                f"quantity={quantity}; est_price={_money(price.amount)}; "
                f"position_value={_money(cost)}; "
                f"portfolio_value={_money(portfolio.value)}"
            ),
        ),
        GateOutcome(
            name="min_order_quantity",
            value=float(quantity),
            threshold=float(min_order_quantity),
            passed=quantity >= min_order_quantity,
            detail=f"whole-share quantity for {item.ticker}",
        ),
        GateOutcome(
            name="max_positions",
            value=float(open_after),
            threshold=float(max_positions),
            passed=(not is_new) or len(open_tickers) < max_positions,
            detail=(
                f"held_positions={_tickers(open_tickers)}; "
                f"is_new_position={str(is_new).lower()}"
            ),
        ),
        GateOutcome(
            name="cash_available",
            value=float(cost),
            threshold=float(available),
            passed=cost <= available,
            detail=(
                f"cash={_money(portfolio.cash.amount)}; "
                f"cash_buffer_pct={float(cash_buffer_pct):.4f}; "
                f"reserved_cash={_money(reserved_cash)}"
            ),
        ),
    )


def position_rejection(
    ticker: str, outcomes: tuple[GateOutcome, ...]
) -> RejectedOrder | None:
    """Preserve the existing PM rejection order and reason strings."""
    reasons = {
        "min_order_quantity": "below_min_quantity",
        "max_positions": "max_positions",
        "cash_available": "insufficient_cash",
    }
    for outcome in outcomes:
        reason = reasons.get(outcome.name)
        if reason is not None and not outcome.passed:
            return RejectedOrder(ticker=ticker, reason=reason)
    return None


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
            passed=stop_pct > 0.0 and ratio >= min_ratio,
            detail=(
                f"target_pct={target_pct:.4f}; stop_pct={stop_pct:.4f}; "
                f"source={_stop_target_source(item)}"
            ),
        ),
    )


def reward_risk_rejection(ticker: str, report: StopTarget) -> RejectedOrder | None:
    """Return the existing reward-risk rejection reason, if any."""
    if report.stop_pct <= 0.0:
        return RejectedOrder(ticker=ticker, reason="invalid_stop_loss")
    if not report.outcome.passed:
        return RejectedOrder(ticker=ticker, reason="reward_risk_below_min")
    return None


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
        stop_pct=report.stop_pct,
        target_pct=report.target_pct,
        rationale=Explanation(
            summary=f"Approved {item.ticker}: sized {quantity} shares from PM policy.",
            evidence_refs=("portfolio_manager.sizing", "provider.regime"),
        ),
        gate_report=outcomes,
    )


def _ratio(numerator: Decimal, denominator: Decimal) -> float:
    if denominator <= 0:
        return 0.0
    return float(numerator / denominator)


def _money(value: Decimal) -> str:
    return f"{value:.2f}"


def _stop_target_source(item: Recommendation) -> str:
    return "recommendation" if item.suggested_stop_pct is not None else "regime"


def _tickers(tickers: set[str]) -> str:
    return ",".join(sorted(tickers)) if tickers else "none"
