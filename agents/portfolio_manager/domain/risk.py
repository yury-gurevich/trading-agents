"""Risk checks for Portfolio Manager order decisions.

Agent: portfolio_manager
Role: approve or reject sized recommendations against portfolio constraints.
External I/O: none.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from agents.portfolio_manager.domain.sizing import size_quantity
from contracts.common import Explanation, Money
from contracts.portfolio_manager import OrderIntent, RejectedOrder

if TYPE_CHECKING:
    from agents.portfolio_manager.portfolio import PortfolioState
    from contracts.analyst import Recommendation


def evaluate_recommendations(
    recommendations: tuple[Recommendation, ...],
    prices: dict[str, Money],
    portfolio: PortfolioState,
    *,
    max_position_pct: Decimal,
    max_positions: int,
    cash_buffer_pct: Decimal,
    min_order_quantity: int,
    default_stop_pct: float,
    default_target_pct: float,
    min_reward_risk_ratio: float,
) -> tuple[tuple[OrderIntent, ...], tuple[RejectedOrder, ...]]:
    """Apply sizing and risk checks in deterministic recommendation order."""
    approved: list[OrderIntent] = []
    rejected: list[RejectedOrder] = []
    reserved_cash = Decimal("0")
    open_tickers = set(portfolio.positions)
    for item in _ordered(recommendations):
        price = prices.get(item.ticker)
        rejection = _precheck(item, price)
        if rejection is not None:
            rejected.append(rejection)
            continue
        assert price is not None
        quantity = size_quantity(
            portfolio_value=portfolio.value,
            max_position_pct=max_position_pct,
            est_price=price.amount,
        )
        rejection = _risk_rejection(
            item=item,
            quantity=quantity,
            price=price,
            portfolio=portfolio,
            reserved_cash=reserved_cash,
            open_tickers=open_tickers,
            max_positions=max_positions,
            cash_buffer_pct=cash_buffer_pct,
            min_order_quantity=min_order_quantity,
        )
        if rejection is not None:
            rejected.append(rejection)
            continue
        stop_pct, target_pct = _effective_pcts(
            item, default_stop_pct, default_target_pct
        )
        rejection = _reward_risk_rejection(
            item, stop_pct, target_pct, min_reward_risk_ratio
        )
        if rejection is not None:
            rejected.append(rejection)
            continue
        approved.append(_order_intent(item, quantity, price, stop_pct, target_pct))
        reserved_cash += Decimal(quantity) * price.amount
        open_tickers.add(item.ticker)
    return tuple(approved), tuple(rejected)


def _ordered(
    recommendations: tuple[Recommendation, ...],
) -> tuple[Recommendation, ...]:
    return tuple(
        sorted(recommendations, key=lambda item: (-item.confidence, item.ticker))
    )


def _precheck(item: Recommendation, price: Money | None) -> RejectedOrder | None:
    if item.action != "buy":
        return RejectedOrder(ticker=item.ticker, reason="unsupported_action")
    if price is None or price.amount <= 0:
        return RejectedOrder(ticker=item.ticker, reason="price_unavailable")
    return None


def _risk_rejection(
    *,
    item: Recommendation,
    quantity: int,
    price: Money,
    portfolio: PortfolioState,
    reserved_cash: Decimal,
    open_tickers: set[str],
    max_positions: int,
    cash_buffer_pct: Decimal,
    min_order_quantity: int,
) -> RejectedOrder | None:
    if quantity < min_order_quantity:
        return RejectedOrder(ticker=item.ticker, reason="below_min_quantity")
    if item.ticker not in open_tickers and len(open_tickers) >= max_positions:
        return RejectedOrder(ticker=item.ticker, reason="max_positions")
    cost = Decimal(quantity) * price.amount
    available = portfolio.cash.amount * (Decimal("1") - cash_buffer_pct) - reserved_cash
    if cost > available:
        return RejectedOrder(ticker=item.ticker, reason="insufficient_cash")
    return None


def _effective_pcts(
    item: Recommendation,
    default_stop_pct: float,
    default_target_pct: float,
) -> tuple[float, float]:
    """Stop/target percentages for this order: the recommendation's or the defaults."""
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
    return stop_pct, target_pct


def _reward_risk_rejection(
    item: Recommendation,
    stop_pct: float,
    target_pct: float,
    min_ratio: float,
) -> RejectedOrder | None:
    """Reject when reward/risk (target_pct / stop_pct) is undefined or too low."""
    if stop_pct <= 0.0:
        return RejectedOrder(ticker=item.ticker, reason="invalid_stop_loss")
    if target_pct / stop_pct < min_ratio:
        return RejectedOrder(ticker=item.ticker, reason="reward_risk_below_min")
    return None


def _order_intent(
    item: Recommendation,
    quantity: int,
    price: Money,
    stop_pct: float,
    target_pct: float,
) -> OrderIntent:
    return OrderIntent(
        ticker=item.ticker,
        action=item.action,
        quantity=quantity,
        est_price=price,
        stop_pct=stop_pct,
        target_pct=target_pct,
        rationale=Explanation(
            summary=f"Approved {item.ticker}: sized {quantity} shares from PM policy.",
            evidence_refs=("portfolio_manager.sizing", "provider.regime"),
        ),
    )
