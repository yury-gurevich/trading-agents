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

from agents.analyst.domain import indicators, indicators_event, indicators_range
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

# A baseline book like the live fleet's (~22 % deployed, several unrelated names), so the PM's sector and
# correlation gates evaluate and print real numbers instead of NOT-EVALUATED. Different wiggle periods
# keep these holdings close to uncorrelated with every candidate. (ticker, sector, wiggle period, phase)
BASELINE_BOOK = (
    ("UTIL", "Utilities", 3.9, 0.4),
    ("BANK", "Financials", 5.3, 2.0),
    ("TELE", "Communication Services", 6.7, 3.1),
    ("REIT", "Real Estate", 8.1, 4.4),
)


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
    supplement: str = ""


def _prov(agent: str) -> Provenance:
    return Provenance(run_id=agent, source_agent=agent)


def build(sc: Scenario) -> Case:
    scanner_s, analyst_s, pm_s, provider_s = fleet_settings()
    spy = bars("SPY", [(300, 0.0005)], start=500.0, phase=0.0, wiggle=0.008, volume=60_000_000)
    # One long history (the forecaster fits ~760 bars); the scanner, analyst and packet use the last 300.
    stock_long = bars(sc.ticker, sc.segments, wiggle=sc.wiggle, phase=sc.phase, n=760)
    stock = stock_long[-300:]
    held = {
        t: bars(t, [(300, 0.0005)], start=140.0, wiggle=0.006, phase=ph, period=per)
        for t, _, per, ph in BASELINE_BOOK
    }
    held |= {t: bars(t, segs, wiggle=sc.wiggle, phase=sc.held_phase) for t, segs in sc.holdings.items()}
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
    # Mirror production (agents/portfolio_manager/graph_portfolio.py): `cash` carries the account EQUITY;
    # true cash, equity and buying power travel in the account_* cents fields.
    cash = Decimal("80000.00")
    equity = cash + sum((v.amount for v in held_values.values()), Decimal("0"))
    portfolio = PortfolioState(
        cash=Money(amount=equity),
        positions={t: 40 for t in held},
        position_values=held_values,
        account_cash_cents=int(cash * 100),
        account_equity_cents=int(equity * 100),
        account_buying_power_cents=int(cash * 100),
    )
    sectors = {sc.ticker: sc.sector, **{t: sec for t, sec, _, _ in BASELINE_BOOK}, **sc.held_sector}
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
    supplement = _supplement(sc, stock, analyst_s, portfolio, held_values, regime, intent)
    supplement += "\n" + _barrier(sc.ticker, stock_long, intent)
    return Case(
        sc.name, sc.ticker, sc.expert_view, True, None, decision, context, dict(score.metrics), supplement
    )


def _barrier(ticker: str, long_bars, intent) -> str:
    """The forecaster's own barrier claim, computed exactly as the live forecaster does (barrier_forecast.py)."""
    import numpy as np
    from agents.forecaster.barrier_fit import ArchGarchFitter
    from agents.forecaster.domain.barrier_garch import (
        HORIZON_SESSIONS,
        accept_fit,
        barrier_seed,
        daily_moves,
        garch_path_probs,
    )
    from agents.forecaster.settings import ForecasterSettings

    head = "Lab supplement, barrier forecast (forecaster GARCH, advisory; skill UNPROVEN, not shown in production): "
    fs = ForecasterSettings()
    if len(long_bars) < fs.barrier_min_history_sessions or not intent.stop_pct or not intent.target_pct:
        return head + "no claim (history or barriers missing)"
    r, lh, ll = daily_moves(
        np.array([b.high for b in long_bars]),
        np.array([b.low for b in long_bars]),
        np.array([b.close for b in long_bars]),
    )
    try:
        params = accept_fit(ArchGarchFitter().fit(r))
    except Exception as e:  # arch missing: the forecaster extra is not installed here
        return head + f"no claim ({type(e).__name__})"
    if params is None:
        return head + "no claim (GARCH fit failed)"
    rng = np.random.default_rng(barrier_seed(ticker, long_bars[-1].bar_date))
    p_stop, p_target, p_neither = garch_path_probs(
        rng,
        params.as_tuple(),
        r,
        lh,
        ll,
        0,
        len(r),
        intent.stop_pct,
        intent.target_pct,
        n_paths=fs.barrier_paths,
    )
    return head + (
        f"barrier_p_stop_first={p_stop:.3f}; barrier_p_target_first={p_target:.3f}; barrier_p_neither={p_neither:.3f}; "
        f"barrier_horizon_sessions={HORIZON_SESSIONS}; barrier_history_bars={len(long_bars)}; barrier_settled_claims=0"
    )


def _f(x: float | None, nd: int = 4) -> str:
    return "n/a" if x is None else f"{x:.{nd}g}"


def _supplement(sc, stock, a, portfolio, held_values, regime, intent) -> str:
    """Numbers the fleet's code computes for this decision but the production packet never shows."""
    closes = [b.close for b in stock]
    highs, lows = [b.high for b in stock], [b.low for b in stock]
    vols = [float(b.volume) for b in stock]
    macd = indicators.macd(closes, a.macd_fast, a.macd_slow, a.macd_signal)
    stoch = indicators_range.stochastic(highs, lows, closes, a.stoch_k_period, a.stoch_d_period)
    obv = indicators_event.obv(closes, vols, a.obv_signal_period)
    w = a.bollinger_window
    mid = indicators._sma(closes, w) if len(closes) >= w else None
    sd = indicators._pstdev(closes[-w:]) if len(closes) >= w else None
    sma_s = (
        indicators._sma(closes, a.golden_cross_short_period)
        if len(closes) >= a.golden_cross_short_period
        else None
    )
    sma_l = indicators._sma(closes, a.sma_long_period) if len(closes) >= a.sma_long_period else None
    ema_s = indicators._ema(closes, a.ema_short_period)
    ema_l = indicators._ema(closes, a.ema_long_period)
    lines = [
        f"Lab supplement, indicator internals for {sc.ticker} (computed by the analyst's code, not shown in "
        f"production): macd_line_price={_f(macd and macd[0])}; macd_signal_price={_f(macd and macd[1])}; "
        f"stochastic_d={_f(stoch and stoch[1])}; obv_signal={_f(obv and obv[1])}; "
        f"sma_{a.golden_cross_short_period}_usd={_f(sma_s)}; sma_{a.sma_long_period}_usd={_f(sma_l)}; "
        f"ema_{a.ema_short_period}_usd={_f(ema_s)}; ema_{a.ema_long_period}_usd={_f(ema_l)}; "
        f"bollinger_middle_usd={_f(mid)}; bollinger_upper_usd={_f(mid and sd is not None and mid + a.bollinger_sigma * sd)}; "
        f"bollinger_lower_usd={_f(mid and sd is not None and mid - a.bollinger_sigma * sd)}",
        f"Lab supplement, portfolio before this order: account_cash_usd={portfolio.account_cash_cents / 100:.2f}; "
        f"account_equity_usd={portfolio.account_equity_cents / 100:.2f}; "
        f"buying_power_usd={portfolio.account_buying_power_cents / 100:.2f}; "
        f"deployed_usd={sum(v.amount for v in held_values.values()):.2f}; open_positions={len(portfolio.positions)}"
        + "".join(
            f"; holding_{t}_shares={q}; holding_{t}_value_usd={held_values[t].amount:.2f}"
            for t, q in portfolio.positions.items()
        ),
        f"Lab supplement, regime data quality: vix_status={regime.vix_status}; vix_as_of={regime.vix_as_of}",
        f"Lab supplement, order: decision_atr_pct={_f(intent.decision_atr_pct)}",
    ]
    return "\n".join(lines)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for sc in SCENARIOS:
        case = build(sc)
        (OUT / f"{sc.name}.json").write_text(json.dumps(asdict(case), indent=2, sort_keys=True) + "\n")
        print(f"{sc.name:26s} reached_referee={case.reached_referee} {case.stopped_at or case.decision}")


if __name__ == "__main__":
    main()
