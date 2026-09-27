"""One-session S235 replay harness stage choreography.

Agent: tooling
Role: call scanner, provider, analyst, and PM domain functions with fixture data.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from agents.analyst.domain.analyze import score_candidates
from agents.analyst.held_universe import scoring_universe
from agents.analyst.result import split_decisions
from agents.portfolio_manager.domain.risk import evaluate_recommendations
from agents.portfolio_manager.portfolio import PortfolioState
from agents.provider.domain.regime import classify_regime
from agents.provider.sources import RegimeInputs
from agents.scanner.domain.filters import apply_filters
from agents.scanner.domain.ranking import rank_survivors
from contracts.analyst import RecommendationSet
from contracts.common import Explanation, Money, Provenance
from contracts.provider import DataQualityTrace, MarketData, OHLCVBar, RegimeContext
from contracts.scanner import CandidateSet
from kernel.errors import CollectingFaultSink

if TYPE_CHECKING:
    from scripts.replay_settings import ReplaySettings

    from contracts.portfolio_manager import OrderIntent, RejectedOrder
    from contracts.positions import OpenPosition, PositionStopThreshold


@dataclass(frozen=True)
class ReplayDayInputs:
    run_id: str
    session: date
    tickers: tuple[str, ...]
    bars: tuple[OHLCVBar, ...]
    benchmark_bars: tuple[OHLCVBar, ...]
    vix: float | None
    equity_cents: int
    held: tuple[OpenPosition, ...]
    held_stops: tuple[PositionStopThreshold, ...]
    active_broker_stop_refs: frozenset[str]
    sectors: dict[str, str]
    position_values: dict[str, Money] = field(default_factory=dict)


@dataclass(frozen=True)
class ReplayDayResult:
    candidates: CandidateSet
    recommendations: RecommendationSet
    approved: tuple[OrderIntent, ...]
    rejected: tuple[RejectedOrder, ...]
    absent_inputs: dict[str, int]


def run_replay_day(
    inputs: ReplayDayInputs, settings: ReplaySettings
) -> ReplayDayResult:
    """Run one replay session by delegating each decision to the fleet domain."""
    bars = tuple(bar for bar in inputs.bars if bar.bar_date <= inputs.session)
    benchmark_bars = tuple(
        bar for bar in inputs.benchmark_bars if bar.bar_date <= inputs.session
    )
    regime_inputs = RegimeInputs(
        as_of=inputs.session,
        vix=inputs.vix,
        vix_status="measured" if inputs.vix is not None else "missing",
        vix_as_of=inputs.session if inputs.vix is not None else None,
    )
    label = classify_regime(regime_inputs, settings.provider)
    regime = RegimeContext(
        label=label,
        vix=inputs.vix,
        vix_status=regime_inputs.vix_status,
        vix_as_of=regime_inputs.vix_as_of,
        as_of=datetime.combine(inputs.session, datetime.min.time(), tzinfo=UTC),
        base_min_confidence=settings.provider.base_min_confidence,
        base_stop_loss_pct=settings.provider.base_stop_loss_pct,
        base_take_profit_pct=settings.provider.base_take_profit_pct,
        base_max_holding_days=settings.provider.base_max_holding_days,
        provenance=Provenance(run_id=inputs.run_id, source_agent="provider"),
    )
    survivors, filter_trace = apply_filters(
        inputs.tickers,
        bars,
        benchmark_bars,
        {},
        inputs.session,
        settings.scanner,
        earnings_horizon_days=None,
    )
    candidates = CandidateSet(
        run_id=inputs.run_id,
        candidates=rank_survivors(survivors, cap=settings.scanner.candidate_cap),
        filter_trace=filter_trace,
        explanation=Explanation(summary="replay scan", evidence_refs=("scanner",)),
        provenance=Provenance(run_id=inputs.run_id, source_agent="scanner"),
    )
    candidates = scoring_universe(candidates, inputs.held)
    market = MarketData(
        bars=bars,
        benchmark=benchmark_bars,
        quality=DataQualityTrace(requested=len(inputs.tickers), returned=len(bars)),
        provenance=Provenance(run_id=inputs.run_id, source_agent="provider"),
        sectors=inputs.sectors,
    )
    sink = CollectingFaultSink()
    decisions = score_candidates(
        candidates,
        market,
        regime,
        benchmark_bars,
        settings.analyst,
        sink,
        held_tickers=tuple(position.ticker for position in inputs.held),
        held_stops=inputs.held_stops,
        active_broker_stop_refs=inputs.active_broker_stop_refs,
    )
    recommendations, rejections = split_decisions(decisions or ())
    recommendation_set = RecommendationSet(
        run_id=inputs.run_id,
        recommendations=recommendations,
        rejections=rejections,
        explanation=Explanation(summary="replay analysis", evidence_refs=("analyst",)),
        provenance=Provenance(run_id=inputs.run_id, source_agent="analyst"),
    )
    approved, rejected = evaluate_recommendations(
        recommendation_set.recommendations,
        _latest_prices(bars),
        PortfolioState(
            cash=Money(amount=Decimal(inputs.equity_cents) / Decimal("100")),
            positions={position.ticker: position.quantity for position in inputs.held},
            position_refs={
                position.ticker: position.position_ref for position in inputs.held
            },
            position_values=inputs.position_values,
        ),
        max_position_pct=settings.portfolio.max_position_pct,
        max_positions=settings.portfolio.max_positions,
        cash_buffer_pct=settings.portfolio.cash_buffer_pct,
        min_order_quantity=settings.portfolio.min_order_quantity,
        default_stop_pct=settings.provider.base_stop_loss_pct,
        default_target_pct=settings.provider.base_take_profit_pct,
        min_reward_risk_ratio=settings.portfolio.min_reward_risk_ratio,
        sectors=inputs.sectors,
        max_sector_pct=settings.portfolio.max_sector_pct,
        max_names_per_sector=settings.portfolio.max_names_per_sector,
        correlation_bars=bars,
        correlation_lookback_days=settings.portfolio.correlation_lookback_days,
        correlation_threshold=settings.portfolio.correlation_threshold,
        correlation_ceiling=settings.portfolio.correlation_ceiling,
        max_correlated_cluster_pct=settings.portfolio.max_correlated_cluster_pct,
        min_correlation_bars=settings.portfolio.min_correlation_bars,
    )
    return ReplayDayResult(
        candidates,
        recommendation_set,
        approved,
        rejected,
        {
            "fundamentals": len(inputs.tickers),
            "news": len(inputs.tickers),
            "sentiment": len(inputs.tickers),
            "earnings": len(inputs.tickers),
            "deliberator": len(inputs.tickers),
        },
    )


def _latest_prices(bars: tuple[OHLCVBar, ...]) -> dict[str, Money]:
    prices: dict[str, Money] = {}
    for bar in sorted(bars, key=lambda item: (item.ticker, item.bar_date)):
        prices[bar.ticker] = Money(amount=Decimal(str(bar.close)))
    return prices
