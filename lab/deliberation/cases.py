"""Build one deliberation case per scenario through the fleet's own code, end to end.

scanner filters -> analyst score + decide -> PM risk gates (fleet settings) -> in-memory graph
lineage -> agents.deliberator.context.build_veto_context. So the packet is byte-for-byte what the
deliberators would receive for this market, and every number is internally consistent.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from agents.analyst.domain.recommend import decide
from agents.analyst.domain.scoring import score_candidate
from agents.deliberator.context import build_veto_context
from agents.portfolio_manager.domain.risk import evaluate_recommendations
from agents.portfolio_manager.portfolio import PortfolioState
from agents.scanner.domain.filters import apply_filters
from agents.scanner.domain.ranking import rank_survivors
from contracts.analyst import RecommendationSet
from contracts.common import Explanation, Money, Provenance
from contracts.portfolio_manager import OrderIntentSet
from contracts.provider import REGIME_CONTEXT_LABEL, DataQualityTrace, MarketData, RegimeContext
from contracts.scanner import CandidateSet
from kernel import InMemoryGraphStore

from .fleet import fleet_settings
from .scenarios import SCENARIOS, Scenario
from .series import END, bars

OUT = Path(__file__).parent / "cases" / "synthetic"


@dataclass
class Case:
    name: str
    ticker: str
    expert_view: str
    reached_referee: bool
    stopped_at: str | None
    decision: str
    context: str
    metrics: dict[str, float]


def _prov(agent: str) -> Provenance:
    return Provenance(run_id=agent, source_agent=agent)


def build(sc: Scenario) -> Case:
    scanner_s, analyst_s, pm_s, provider_s = fleet_settings()
    spy = bars("SPY", [(300, 0.0005)], start=500.0, phase=0.0, wiggle=0.008, volume=60_000_000)
    stock = bars(sc.ticker, sc.segments, wiggle=sc.wiggle, phase=sc.phase)
    held = {t: bars(t, segs, wiggle=sc.wiggle, phase=sc.phase) for t, segs in sc.holdings.items()}
    all_bars = stock + tuple(b for series in held.values() for b in series)
    earnings = {sc.ticker: END + timedelta(days=sc.earnings_in_days)}

    def stop(where: str) -> Case:
        return Case(sc.name, sc.ticker, sc.expert_view, False, where, "", "", {})

    survivors, trace = apply_filters((sc.ticker,), stock, spy, earnings, END, scanner_s)
    if not survivors:
        return stop(f"scanner: {trace.dropped_by_filter}")
    candidates = rank_survivors(survivors, cap=scanner_s.candidate_cap)
    cand = candidates[0]
    score = score_candidate(cand, stock, sc.fundamentals, spy, sc.news, analyst_s)
    as_of = datetime.combine(END, datetime.min.time(), tzinfo=UTC)
    regime = RegimeContext(
        label=sc.regime,
        vix=sc.vix,
        vix_status="measured",
        vix_as_of=END,
        as_of=as_of,
        base_min_confidence=provider_s.base_min_confidence,
        base_stop_loss_pct=provider_s.base_stop_loss_pct,
        base_take_profit_pct=provider_s.base_take_profit_pct,
        base_max_holding_days=provider_s.base_max_holding_days,
        provenance=_prov("provider"),
    )
    verdict = decide(cand, score, regime, settings=analyst_s)
    rec = verdict.recommendation
    if rec is None or rec.action != "buy":
        reason = verdict.rejection.reason if verdict.rejection else (rec.action if rec else "none")
        c = stop(f"analyst: {reason}")
        c.metrics = dict(score.metrics)
        return c
    held_values = {t: Money(amount=Decimal(str(round(s[-1].close * 40, 2)))) for t, s in held.items()}
    portfolio = PortfolioState(
        cash=Money(amount=Decimal("80000.00")), positions={t: 40 for t in held}, position_values=held_values
    )
    sectors = {sc.ticker: sc.sector, **sc.held_sector}
    approved, rejected = evaluate_recommendations(
        (rec,),
        {sc.ticker: Money(amount=Decimal(str(stock[-1].close)))},
        portfolio,
        max_position_pct=pm_s.max_position_pct,
        max_positions=pm_s.max_positions,
        cash_buffer_pct=pm_s.cash_buffer_pct,
        min_order_quantity=pm_s.min_order_quantity,
        default_stop_pct=regime.base_stop_loss_pct,
        default_target_pct=regime.base_take_profit_pct,
        min_reward_risk_ratio=pm_s.min_reward_risk_ratio,
        sectors=sectors,
        max_sector_pct=pm_s.max_sector_pct,
        max_names_per_sector=pm_s.max_names_per_sector,
        correlation_bars=all_bars,
        correlation_lookback_days=pm_s.correlation_lookback_days,
        correlation_threshold=pm_s.correlation_threshold,
        correlation_ceiling=pm_s.correlation_ceiling,
        max_correlated_cluster_pct=pm_s.max_correlated_cluster_pct,
        min_correlation_bars=pm_s.min_correlation_bars,
    )
    if not approved:
        c = stop(f"pm: {rejected[0].reason if rejected else 'no order'}")
        c.metrics = dict(score.metrics)
        return c
    intent = approved[0]
    graph = InMemoryGraphStore()
    market = MarketData(
        bars=all_bars,
        benchmark=spy,
        fundamentals={sc.ticker: sc.fundamentals},
        news={sc.ticker: sc.news},
        sentiment={sc.ticker: sc.provider_sentiment},
        sectors=sectors,
        earnings=earnings,
        quality=DataQualityTrace(
            requested=1 + len(held),
            returned=1 + len(held),
            used_fallback=False,
            stale_tickers=(),
            anomalous_tickers=(),
            notes=(),
        ),
        provenance=_prov("provider"),
    )
    m = graph.merge_node(
        "MarketData", "market", {"run_id": "market", "snapshot": market.model_dump(mode="json")}
    )
    graph.merge_node(
        REGIME_CONTEXT_LABEL, "regime-context:market", {"snapshot": regime.model_dump(mode="json")}
    )
    scan = graph.merge_node(
        "ScanRun",
        "scan",
        {
            "candidate_set": CandidateSet(
                run_id="scan",
                candidates=candidates,
                filter_trace=trace,
                explanation=Explanation(summary="scanner"),
                provenance=_prov("scanner"),
            ).model_dump(mode="json")
        },
    )
    graph.add_edge(scan, m, "DERIVED_FROM")
    analyst = graph.merge_node(
        "AnalystRun",
        "analyst",
        {
            "recommendation_set": RecommendationSet(
                run_id="analyst",
                recommendations=(rec,),
                rejections=(),
                explanation=Explanation(summary="analyst"),
                provenance=_prov("analyst"),
            ).model_dump(mode="json")
        },
    )
    graph.add_edge(scan, analyst, "ANALYZED_BY")
    pm = graph.merge_node("PMRun", "pm", {})
    graph.add_edge(analyst, pm, "EVALUATED_BY")
    orders = OrderIntentSet(
        run_id="pm",
        approved=(intent,),
        rejected=(),
        explanation=Explanation(summary="pm"),
        provenance=_prov("portfolio_manager"),
    )
    context = build_veto_context(graph, pm, orders, intent)
    decision = f"{intent.action} {intent.ticker} (qty {intent.quantity})"
    return Case(sc.name, sc.ticker, sc.expert_view, True, None, decision, context, dict(score.metrics))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for sc in SCENARIOS:
        case = build(sc)
        (OUT / f"{sc.name}.json").write_text(json.dumps(asdict(case), indent=2, sort_keys=True) + "\n")
        print(f"{sc.name:26s} reached_referee={case.reached_referee} {case.stopped_at or case.decision}")


if __name__ == "__main__":
    main()
