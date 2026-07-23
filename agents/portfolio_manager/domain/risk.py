"""Risk checks for Portfolio Manager order decisions.

Agent: portfolio_manager
Role: approve or reject sized recommendations against portfolio constraints.
External I/O: none.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from agents.portfolio_manager.domain.concentration import SectorBook
from agents.portfolio_manager.domain.exits import exit_order_intent, exit_outcomes
from agents.portfolio_manager.domain.gate_report import (
    order_intent,
    position_outcomes,
    position_rejection,
    reward_risk_rejection,
    stop_target_report,
)
from agents.portfolio_manager.domain.sizing import size_quantity
from contracts.portfolio_manager import GateOutcome, RejectedOrder

if TYPE_CHECKING:
    from agents.portfolio_manager.portfolio import PortfolioState
    from contracts.analyst import Recommendation
    from contracts.common import Money
    from contracts.portfolio_manager import OrderIntent


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
    sectors: dict[str, str] | None = None,
    max_sector_pct: Decimal = Decimal("1"),
    max_names_per_sector: int = 0,
) -> tuple[tuple[OrderIntent, ...], tuple[RejectedOrder, ...]]:
    """Apply sizing and risk checks in deterministic recommendation order."""
    sectors_map = sectors or {}
    approved: list[OrderIntent] = []
    rejected: list[RejectedOrder] = []
    reserved_cash = Decimal("0")
    book = SectorBook(sectors_map, portfolio.positions)
    open_tickers = set(portfolio.positions)
    for item in _ordered(recommendations):
        price = prices.get(item.ticker)
        rejection = _precheck(item, price, portfolio)
        if rejection is not None:
            rejected.append(rejection)
            continue
        assert price is not None
        if item.action == "sell":
            quantity = portfolio.positions[item.ticker]
            gates = exit_outcomes(
                item=item,
                quantity=quantity,
                price=price,
                portfolio=portfolio,
                min_order_quantity=min_order_quantity,
                max_positions=max_positions,
            )
            rejection = position_rejection(item.ticker, gates)
            if rejection is not None:
                rejected.append(rejection)
                continue
            sector_gates = book.exit_outcomes(item, max_names_per_sector)
            approved.append(
                exit_order_intent(item, quantity, price, (*gates, *sector_gates))
            )
            open_tickers.discard(item.ticker)
            book.record_exit(item.ticker)
            continue
        quantity = size_quantity(
            portfolio_value=portfolio.value,
            max_position_pct=max_position_pct,
            est_price=price.amount,
        )
        gates = position_outcomes(
            item=item,
            quantity=quantity,
            price=price,
            portfolio=portfolio,
            reserved_cash=reserved_cash,
            open_tickers=open_tickers,
            max_position_pct=max_position_pct,
            max_positions=max_positions,
            cash_buffer_pct=cash_buffer_pct,
            min_order_quantity=min_order_quantity,
        )
        rejection = position_rejection(item.ticker, gates)
        if rejection is not None:
            rejected.append(rejection)
            continue
        stop_target = stop_target_report(
            item, default_stop_pct, default_target_pct, min_reward_risk_ratio
        )
        rejection = reward_risk_rejection(item.ticker, stop_target)
        if rejection is not None:
            rejected.append(rejection)
            continue
        cost = Decimal(quantity) * price.amount
        sector_gates = book.outcomes(
            item,
            cost,
            portfolio.value,
            max_sector_pct=max_sector_pct,
            max_names_per_sector=max_names_per_sector,
        )
        rejection = _sector_rejection(item.ticker, sector_gates)
        if rejection is not None:
            rejected.append(rejection)
            continue
        gate_report = (*gates, stop_target.outcome, *sector_gates)
        approved.append(order_intent(item, quantity, price, stop_target, gate_report))
        reserved_cash += cost
        open_tickers.add(item.ticker)
        book.record(item, cost)
    return tuple(approved), tuple(rejected)


def _ordered(
    recommendations: tuple[Recommendation, ...],
) -> tuple[Recommendation, ...]:
    return tuple(
        sorted(
            recommendations,
            key=lambda item: (_action_rank(item.action), -item.confidence, item.ticker),
        )
    )


def _action_rank(action: str) -> int:
    if action == "sell":
        return 0
    if action == "buy":
        return 1
    return 2


def _precheck(
    item: Recommendation, price: Money | None, portfolio: PortfolioState
) -> RejectedOrder | None:
    if item.action == "hold":
        return RejectedOrder(ticker=item.ticker, reason="hold_recommendation")
    if item.action not in ("buy", "sell"):
        return RejectedOrder(ticker=item.ticker, reason="unsupported_action")
    if item.action == "sell" and item.ticker not in portfolio.positions:
        return RejectedOrder(ticker=item.ticker, reason="position_unavailable")
    if price is None or price.amount <= 0:
        return RejectedOrder(ticker=item.ticker, reason="price_unavailable")
    return None


def _sector_rejection(
    ticker: str, outcomes: tuple[GateOutcome, ...]
) -> RejectedOrder | None:
    for outcome in outcomes:
        if outcome.name == "max_names_per_sector" and not outcome.passed:
            return RejectedOrder(ticker=ticker, reason="sector_name_count")
        if outcome.name == "max_sector_pct" and not outcome.passed:
            return RejectedOrder(ticker=ticker, reason="sector_concentration")
    return None
