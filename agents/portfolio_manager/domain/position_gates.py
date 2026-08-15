"""Entry gate outcomes, and the gate-to-rejection-reason mapping.

Agent: portfolio_manager
Role: report the sizing, quantity, name-count and cash gates for a sized order,
      and map the first failing gate — sizing or sector — to the rejection reason
      the PM has always used.
External I/O: none.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from contracts.portfolio_manager import GateOutcome, RejectedOrder

if TYPE_CHECKING:
    from agents.portfolio_manager.portfolio import PortfolioState
    from contracts.analyst import Recommendation
    from contracts.common import Money


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
    available = portfolio.available_for_buys(cash_buffer_pct, reserved_cash)
    is_new = item.ticker not in open_tickers
    open_after = len(open_tickers) + int(is_new)
    return (
        GateOutcome(
            name="sizing",
            value=_ratio(cost, portfolio.value),
            threshold=float(max_position_pct),
            passed=cost <= max_position_pct * portfolio.value,
            detail=(
                f"quantity_shares={quantity}; est_price_usd={_money(price.amount)}; "
                f"position_value_usd={_money(cost)}; "
                f"portfolio_value_usd={_money(portfolio.value)}"
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
                f"portfolio_value_usd={_money(portfolio.value)}; "
                f"deployed_portfolio_usd={_money(portfolio.deployed_value)}; "
                f"cash_buffer_pct={float(cash_buffer_pct):.4f}; "
                f"reserved_cash_this_batch_usd={_money(reserved_cash)}"
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
            return RejectedOrder(ticker=ticker, reason=reason, gate_report=outcomes)
    return None


def sector_rejection(
    ticker: str,
    outcomes: tuple[GateOutcome, ...],
    prior_outcomes: tuple[GateOutcome, ...],
) -> RejectedOrder | None:
    """Map a failing sector gate to its reason, keeping the evaluated evidence."""
    gate_report = (*prior_outcomes, *outcomes)
    for outcome in outcomes:
        if outcome.name == "max_names_per_sector" and not outcome.passed:
            return RejectedOrder(
                ticker=ticker,
                reason="sector_name_count",
                gate_report=gate_report,
            )
        if outcome.name == "max_sector_pct" and not outcome.passed:
            return RejectedOrder(
                ticker=ticker,
                reason="sector_concentration",
                gate_report=gate_report,
            )
    return None


def _ratio(numerator: Decimal, denominator: Decimal) -> float:
    return 0.0 if denominator <= 0 else float(numerator / denominator)


def _money(value: Decimal) -> str:
    return f"{value:.2f}"


def _tickers(tickers: set[str]) -> str:
    return ",".join(sorted(tickers)) if tickers else "none"
