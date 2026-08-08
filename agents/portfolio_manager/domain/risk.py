"""Risk checks for Portfolio Manager order decisions.

Agent: portfolio_manager
Role: approve or reject sized recommendations against portfolio constraints.
External I/O: none.

The per-recommendation exit and entry decisions live in `order_decision`; this
module owns the deterministic ordering, the precheck, and the running book state
carried across recommendations.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from agents.portfolio_manager.domain.concentration import SectorBook
from agents.portfolio_manager.domain.order_decision import decide_entry, decide_exit
from contracts.portfolio_manager import OrderIntent, RejectedOrder

if TYPE_CHECKING:
    from agents.portfolio_manager.portfolio import PortfolioState
    from contracts.analyst import Recommendation
    from contracts.common import Money


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
            decision = decide_exit(
                item,
                price,
                portfolio,
                book,
                min_order_quantity=min_order_quantity,
                max_positions=max_positions,
                max_names_per_sector=max_names_per_sector,
            )
            if isinstance(decision, RejectedOrder):
                rejected.append(decision)
                continue
            approved.append(decision)
            open_tickers.discard(item.ticker)
            book.record_exit(item.ticker)
            continue
        decision, cost = decide_entry(
            item,
            price,
            portfolio,
            book,
            reserved_cash=reserved_cash,
            open_tickers=open_tickers,
            max_position_pct=max_position_pct,
            max_positions=max_positions,
            cash_buffer_pct=cash_buffer_pct,
            min_order_quantity=min_order_quantity,
            default_stop_pct=default_stop_pct,
            default_target_pct=default_target_pct,
            min_reward_risk_ratio=min_reward_risk_ratio,
            max_sector_pct=max_sector_pct,
            max_names_per_sector=max_names_per_sector,
        )
        if isinstance(decision, RejectedOrder):
            rejected.append(decision)
            continue
        approved.append(decision)
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
    if item.action == "buy" and not portfolio.account_is_fresh:
        return RejectedOrder(ticker=item.ticker, reason="account_unavailable")
    if price is None or price.amount <= 0:
        return RejectedOrder(ticker=item.ticker, reason="price_unavailable")
    return None
