"""Per-recommendation exit and entry decisions for the Portfolio Manager.

Agent: portfolio_manager
Role: decide one prechecked recommendation — an approved OrderIntent or the
      RejectedOrder naming the first gate that blocked it, gates evaluated in the
      established order so reason strings and evidence are unchanged.
External I/O: none.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from agents.portfolio_manager.domain.exits import exit_order_intent, exit_outcomes
from agents.portfolio_manager.domain.gate_report import (
    order_intent,
    reward_risk_rejection,
    stop_target_report,
)
from agents.portfolio_manager.domain.position_gates import (
    position_outcomes,
    position_rejection,
    sector_rejection,
)
from agents.portfolio_manager.domain.sizing import size_quantity

if TYPE_CHECKING:
    from agents.portfolio_manager.domain.concentration import SectorBook
    from agents.portfolio_manager.domain.correlation import CorrelationBook
    from agents.portfolio_manager.portfolio import PortfolioState
    from contracts.analyst import Recommendation
    from contracts.common import Money
    from contracts.portfolio_manager import OrderIntent, RejectedOrder


def decide_exit(
    item: Recommendation,
    price: Money,
    portfolio: PortfolioState,
    book: SectorBook,
    *,
    min_order_quantity: int,
    max_positions: int,
    max_names_per_sector: int,
) -> OrderIntent | RejectedOrder:
    """Decide a sell of the full held quantity."""
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
        return rejection
    sector_gates = book.exit_outcomes(item, max_names_per_sector)
    return exit_order_intent(
        item,
        quantity,
        price,
        (*gates, *sector_gates),
        portfolio.position_refs.get(item.ticker),
    )


def decide_entry(
    item: Recommendation,
    price: Money,
    portfolio: PortfolioState,
    book: SectorBook,
    *,
    reserved_cash: Decimal,
    open_issuers: set[str],
    max_position_pct: Decimal,
    max_positions: int,
    cash_buffer_pct: Decimal,
    min_order_quantity: int,
    default_stop_pct: float,
    default_target_pct: float,
    min_reward_risk_ratio: float,
    max_sector_pct: Decimal,
    max_names_per_sector: int,
    correlations: CorrelationBook,
) -> tuple[OrderIntent | RejectedOrder, Decimal]:
    """Decide a buy, returning the decision and the cash it would commit."""
    quantity = size_quantity(
        portfolio_value=portfolio.value,
        max_position_pct=max_position_pct,
        est_price=price.amount,
    )
    issuer = book.issuer_for(item.ticker)
    gates = position_outcomes(
        item=item,
        quantity=quantity,
        price=price,
        portfolio=portfolio,
        reserved_cash=reserved_cash,
        open_issuers=open_issuers,
        issuer=issuer,
        existing_issuer_value=book.issuer_value(issuer),
        max_position_pct=max_position_pct,
        max_positions=max_positions,
        cash_buffer_pct=cash_buffer_pct,
        min_order_quantity=min_order_quantity,
    )
    rejection = position_rejection(item.ticker, gates)
    if rejection is not None:
        return rejection, Decimal("0")
    stop_target = stop_target_report(
        item, default_stop_pct, default_target_pct, min_reward_risk_ratio
    )
    rejection = reward_risk_rejection(item.ticker, stop_target, gates)
    if rejection is not None:
        return rejection, Decimal("0")
    cost = Decimal(quantity) * price.amount
    sector_gates = book.outcomes(
        item,
        cost,
        portfolio.value,
        max_sector_pct=max_sector_pct,
        max_names_per_sector=max_names_per_sector,
    )
    rejection = sector_rejection(
        item.ticker, sector_gates, (*gates, stop_target.outcome)
    )
    if rejection is not None:
        return rejection, Decimal("0")
    gate_report = (*gates, stop_target.outcome, *sector_gates)
    correlation_gates = correlations.outcomes(
        item,
        cost,
        portfolio.value,
        issuer_values=book.issuer_values(),
        issuer_tickers=book.issuer_tickers(),
    )
    rejection = sector_rejection(
        item.ticker,
        correlation_gates,
        gate_report,
    )
    if rejection is not None:
        return rejection, Decimal("0")
    gate_report = (*gate_report, *correlation_gates)
    return order_intent(item, quantity, price, stop_target, gate_report), cost
