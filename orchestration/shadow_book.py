"""Read-only recommendation outcome derivation over persisted run facts.

Agent: orchestration
Role: join analyst decisions to their market snapshots and recorded PM dispositions.
External I/O: GraphStore reads via the injected backend; never writes.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import TYPE_CHECKING, Literal

from contracts.provider import MARKET_DATA_LABEL
from orchestration.shadow_book_join import (
    pm_orders_by_analyst,
    recommendations_by_analyst,
)
from orchestration.shadow_book_prices import (
    market_history,
    reference_price,
    source_market,
    target_date,
)

if TYPE_CHECKING:
    from contracts.portfolio_manager import OrderIntentSet
    from contracts.provider import MarketData
    from kernel import GraphStore, Node

Disposition = Literal["taken", "blocked_capacity", "blocked_other", "not_actionable"]
OutcomeStatus = Literal["scored", "unpriceable", "not_yet_elapsed"]

_ANALYST_RUN_LABEL = "AnalystRun"
_CAPACITY_REASON = "max_positions"


@dataclass(frozen=True)
class ShadowOutcome:
    """One recommendation evaluated at one forward trading-day horizon."""

    recommendation_ref: str
    analyst_run_id: str
    as_of: date
    ticker: str
    action: str
    confidence: float
    technical_score: float
    horizon: int
    disposition: Disposition
    disposition_reason: str | None
    status: OutcomeStatus
    reference_price: float | None
    forward_price: float | None
    forward_return: float | None


def derive_shadow_book(
    graph: GraphStore, horizons: tuple[int, ...]
) -> tuple[ShadowOutcome, ...]:
    """Reconstruct all recommendation outcomes without mutating the graph."""
    if not horizons or any(horizon < 1 for horizon in horizons):
        raise ValueError("horizons must contain positive trading-day counts")
    analyst_runs = sorted(
        graph.list_nodes(_ANALYST_RUN_LABEL),
        key=lambda node: (str(node.props.get("created_at", "")), node.key),
    )
    recommendations = recommendations_by_analyst(graph, tuple(analyst_runs))
    history, trading_dates = market_history(graph.list_nodes(MARKET_DATA_LABEL))
    pm_orders = pm_orders_by_analyst(graph)
    outcomes: list[ShadowOutcome] = []
    for analyst_run in analyst_runs:
        run_recommendations = recommendations[analyst_run.key]
        if not run_recommendations:
            continue
        market = source_market(graph, analyst_run)
        as_of = datetime.fromisoformat(str(analyst_run.props["created_at"])).date()
        orders = pm_orders.get(analyst_run.key)
        for recommendation in run_recommendations:
            outcomes.extend(
                _recommendation_outcomes(
                    analyst_run,
                    recommendation,
                    market,
                    orders,
                    history,
                    trading_dates,
                    as_of,
                    horizons,
                )
            )
    return tuple(outcomes)


def _recommendation_outcomes(
    analyst_run: Node,
    recommendation: Node,
    market: MarketData | None,
    orders: OrderIntentSet | None,
    history: dict[str, dict[date, float]],
    trading_dates: tuple[date, ...],
    as_of: date,
    horizons: tuple[int, ...],
) -> list[ShadowOutcome]:
    ticker = str(recommendation.props["ticker"])
    reference = reference_price(market, ticker, as_of)
    disposition, reason = _disposition(ticker, orders)
    return [
        _outcome(
            analyst_run,
            recommendation,
            horizon,
            reference,
            history,
            trading_dates,
            as_of,
            disposition,
            reason,
        )
        for horizon in horizons
    ]


def _outcome(
    analyst_run: Node,
    recommendation: Node,
    horizon: int,
    reference: float | None,
    history: dict[str, dict[date, float]],
    trading_dates: tuple[date, ...],
    as_of: date,
    disposition: Disposition,
    reason: str | None,
) -> ShadowOutcome:
    ticker = str(recommendation.props["ticker"])
    target = target_date(trading_dates, as_of, horizon)
    forward = history.get(ticker, {}).get(target) if target else None
    if reference is None:
        status: OutcomeStatus = "unpriceable"
    elif target is None:
        status = "not_yet_elapsed"
    elif forward is None:
        status = "unpriceable"
    else:
        status = "scored"
    forward_return = (
        (forward / reference) - 1.0
        if status == "scored" and forward is not None and reference is not None
        else None
    )
    return ShadowOutcome(
        recommendation_ref=f"{recommendation.label}:{recommendation.key}",
        analyst_run_id=analyst_run.key,
        as_of=as_of,
        ticker=ticker,
        action=str(recommendation.props["action"]),
        confidence=float(recommendation.props["confidence"]),
        technical_score=float(recommendation.props["technical_score"]),
        horizon=horizon,
        disposition=disposition,
        disposition_reason=reason,
        status=status,
        reference_price=reference,
        forward_price=forward if status == "scored" else None,
        forward_return=forward_return,
    )


def _disposition(
    ticker: str, orders: OrderIntentSet | None
) -> tuple[Disposition, str | None]:
    if orders is None:
        return "not_actionable", None
    if any(order.ticker == ticker for order in orders.approved):
        return "taken", None
    reason = next(
        (item.reason for item in orders.rejected if item.ticker == ticker), None
    )
    if reason == _CAPACITY_REASON:
        return "blocked_capacity", reason
    if reason is not None:
        return "blocked_other", reason
    return "not_actionable", None
