"""Evidence renderer for the deliberation challenger-veto.

Agent: orchestration
Role: turn the provider→scanner→analyst→PM graph lineage into compact debate context.
External I/O: none (reads the injected GraphStore).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from contracts.analyst import Recommendation, RecommendationSet
from contracts.provider import REGIME_CONTEXT_LABEL, MarketData, OHLCVBar, RegimeContext
from contracts.scanner import Candidate, CandidateSet, FilterVerdict

if TYPE_CHECKING:
    from collections.abc import Iterable

    from contracts.common import Explanation
    from contracts.portfolio_manager import OrderIntent, OrderIntentSet
    from kernel import GraphStore, Node

_ANALYZED_EDGE = "ANALYZED_BY"
_DERIVED_FROM = "DERIVED_FROM"
_EVALUATED_EDGE = "EVALUATED_BY"


def build_veto_context(
    graph: GraphStore, pm_node: Node, order_set: OrderIntentSet, intent: OrderIntent
) -> str:
    """Render all available upstream evidence for one PM-approved order."""
    lines = [
        f"Run {order_set.run_id}: PM-approved order under challenger-veto review.",
        _order_line(intent),
        f"PM run: {_explain(order_set.explanation)}",
    ]
    analyst = _first(
        graph.ancestors(pm_node, max_depth=1, edge_types={_EVALUATED_EDGE})
    )
    if analyst is None:
        return "\n".join((*lines, "Lineage: no AnalystRun linked to this PMRun."))
    recs = RecommendationSet.model_validate(analyst.props["recommendation_set"])
    lines.extend(_analyst_lines(recs, intent.ticker))
    scan = _first(graph.ancestors(analyst, max_depth=1, edge_types={_ANALYZED_EDGE}))
    if scan is None:
        return "\n".join((*lines, "Lineage: no ScanRun linked to this AnalystRun."))
    candidates = CandidateSet.model_validate(scan.props["candidate_set"])
    lines.extend(_scanner_lines(candidates, intent.ticker))
    market_node = _first(
        graph.descendants(scan, max_depth=1, edge_types={_DERIVED_FROM})
    )
    if market_node is None:
        return "\n".join((*lines, "Lineage: no MarketData linked to this ScanRun."))
    market = MarketData.model_validate(market_node.props["snapshot"])
    lines.extend(_market_lines(market, intent.ticker))
    regime = _regime(graph, market_node)
    if regime is not None:
        lines.append(
            "Regime: "
            f"label={regime.label}; vix={regime.vix}; "
            f"base_min_confidence={regime.base_min_confidence:.3f}; "
            f"base_stop_loss_pct={_pct(regime.base_stop_loss_pct)}; "
            f"base_take_profit_pct={_pct(regime.base_take_profit_pct)}; "
            f"base_max_holding_days={regime.base_max_holding_days}"
        )
    return "\n".join(lines)


def _analyst_lines(recs: RecommendationSet, ticker: str) -> list[str]:
    rec = next((item for item in recs.recommendations if item.ticker == ticker), None)
    lines = [f"Analyst run: {_explain(recs.explanation)}"]
    if rec is not None:
        lines.append(_recommendation_line(rec))
    for rejection in recs.rejections:
        if rejection.ticker == ticker:
            lines.append(f"Analyst rejected {ticker}: {rejection.reason}")
    return lines


def _scanner_lines(candidates: CandidateSet, ticker: str) -> list[str]:
    candidate = next(
        (item for item in candidates.candidates if item.ticker == ticker), None
    )
    lines = [
        f"Scanner run: {_explain(candidates.explanation)}",
        "Scanner filter trace: "
        f"universe_size={candidates.filter_trace.universe_size}; "
        f"evaluated={candidates.filter_trace.evaluated}; "
        f"dropped_by_filter={dict(candidates.filter_trace.dropped_by_filter)}",
    ]
    if candidate is not None:
        lines.append(_candidate_line(candidate))
    verdict = _verdict(candidates.filter_trace.verdicts, ticker)
    if verdict is not None:
        lines.append(
            f"Scanner verdict for {ticker}: decision={verdict.decision}; "
            f"filter_fired={verdict.filter_fired}; bypassed={verdict.bypassed}; "
            f"features={_dict(verdict.features)}"
        )
    return lines


def _market_lines(market: MarketData, ticker: str) -> list[str]:
    lines = [
        "Market data quality: "
        f"requested={market.quality.requested}; returned={market.quality.returned}; "
        f"used_fallback={market.quality.used_fallback}; "
        f"stale_tickers={list(market.quality.stale_tickers)}; "
        f"anomalous_tickers={list(market.quality.anomalous_tickers)}; "
        f"notes={list(market.quality.notes)}",
    ]
    bar = _latest_bar(market.bars, ticker)
    if bar is not None:
        lines.append(
            f"Latest OHLCV for {ticker}: date={bar.bar_date}; open={bar.open:.4g}; "
            f"high={bar.high:.4g}; low={bar.low:.4g}; close={bar.close:.4g}; "
            f"volume={bar.volume}"
        )
    if ticker in market.fundamentals:
        lines.append(f"Fundamentals for {ticker}: {_dict(market.fundamentals[ticker])}")
    if ticker in market.sentiment:
        lines.append(f"Provider sentiment for {ticker}: {market.sentiment[ticker]:.3f}")
    if ticker in market.sectors:
        lines.append(f"Sector for {ticker}: {market.sectors[ticker]}")
    if ticker in market.earnings:
        lines.append(f"Next earnings for {ticker}: {market.earnings[ticker]}")
    if ticker in market.news:
        lines.append(f"News for {ticker}: {' | '.join(market.news[ticker])}")
    return lines


def _order_line(intent: OrderIntent) -> str:
    return (
        f"PM order: action={intent.action}; ticker={intent.ticker}; "
        f"quantity={intent.quantity}; est_price={intent.est_price.amount} "
        f"{intent.est_price.currency}; stop_pct={_pct(intent.stop_pct)}; "
        f"target_pct={_pct(intent.target_pct)}; rationale={_explain(intent.rationale)}"
    )


def _recommendation_line(rec: Recommendation) -> str:
    return (
        f"Analyst recommendation for {rec.ticker}: action={rec.action}; "
        f"confidence={rec.confidence:.3f}; technical_score={rec.technical_score:.3f}; "
        f"sentiment_score={_num(rec.sentiment_score)}; "
        f"fundamental_score={_num(rec.fundamental_score)}; "
        f"suggested_stop_pct={_pct(rec.suggested_stop_pct)}; "
        f"suggested_target_pct={_pct(rec.suggested_target_pct)}; "
        f"rationale={_explain(rec.rationale)}"
    )


def _candidate_line(candidate: Candidate) -> str:
    return (
        f"Scanner candidate for {candidate.ticker}: rank={candidate.rank}; "
        f"score={candidate.score:.3f}; "
        f"survived_filters={list(candidate.survived_filters)}; "
        f"metrics={_dict(candidate.metrics)}"
    )


def _regime(graph: GraphStore, market_node: Node) -> RegimeContext | None:
    key = f"regime-context:{market_node.props['run_id']}"
    node = graph.get_node(REGIME_CONTEXT_LABEL, key)
    return RegimeContext.model_validate(node.props["snapshot"]) if node else None


def _verdict(items: tuple[FilterVerdict, ...], ticker: str) -> FilterVerdict | None:
    return next((item for item in items if item.ticker == ticker), None)


def _latest_bar(items: tuple[OHLCVBar, ...], ticker: str) -> OHLCVBar | None:
    bars = [item for item in items if item.ticker == ticker]
    return max(bars, key=lambda item: item.bar_date) if bars else None


def _first(items: Iterable[Node]) -> Node | None:
    return next(iter(items), None)


def _explain(value: Explanation) -> str:
    refs = f" refs={list(value.evidence_refs)}" if value.evidence_refs else ""
    return f"{value.summary}{refs}"


def _dict(values: dict[str, float]) -> str:
    return "{" + ", ".join(f"{key}={values[key]:.4g}" for key in sorted(values)) + "}"


def _num(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.3f}"


def _pct(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.2%}"
