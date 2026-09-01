"""Evidence renderer for the deliberator.

Agent: deliberator
Role: turn provider -> scanner -> analyst -> PM graph lineage into debate context.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.deliberator.context_market import market_lines, regime_context
from agents.deliberator.context_pm import (
    order_lines,
    recommendation_line,
    regime_gate_lines,
)
from agents.deliberator.context_values import (
    SOURCE_VALUE_BOUNDARY,
    explain,
    source_metric_map,
)
from contracts.analyst import Recommendation, RecommendationSet
from contracts.provider import MarketData
from contracts.scanner import Candidate, CandidateSet, FilterVerdict

if TYPE_CHECKING:
    from collections.abc import Iterable

    from contracts.portfolio_manager import OrderIntent, OrderIntentSet
    from kernel import GraphStore, Node

_ANALYZED_EDGE = "ANALYZED_BY"
_DERIVED_FROM = "DERIVED_FROM"
_EVALUATED_EDGE = "EVALUATED_BY"
_PORTFOLIO_BATCH_BOUNDARY = (
    "Portfolio/batch context: unavailable; this packet contains no holdings, "
    "open positions, sibling orders, or dual-class exposure facts. Reviewers must "
    "not infer them beyond the explicit PM gate outcomes rendered below."
)


def build_veto_context(
    graph: GraphStore, pm_node: Node, order_set: OrderIntentSet, intent: OrderIntent
) -> str:
    """Render all available upstream evidence for one PM-approved order."""
    lines = [
        f"Run {order_set.run_id}: PM-approved order under challenger-veto review.",
        _PORTFOLIO_BATCH_BOUNDARY,
        SOURCE_VALUE_BOUNDARY,
        *order_lines(intent),
        f"PM run: {explain(order_set.explanation)}",
    ]
    analyst = _first(
        graph.ancestors(pm_node, max_depth=1, edge_types={_EVALUATED_EDGE})
    )
    if analyst is None:
        return "\n".join((*lines, "Lineage: no AnalystRun linked to this PMRun."))
    recs = RecommendationSet.model_validate(analyst.props["recommendation_set"])
    rec = _recommendation(recs, intent.ticker)
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
    lines.extend(market_lines(market, intent.ticker))
    regime = regime_context(graph, market_node)
    lines.extend(regime_gate_lines(regime, rec, intent, market.bars))
    return "\n".join(lines)


def _analyst_lines(recs: RecommendationSet, ticker: str) -> list[str]:
    rec = _recommendation(recs, ticker)
    lines = [f"Analyst run: {explain(recs.explanation)}"]
    if rec is not None:
        lines.append(recommendation_line(rec))
    for rejection in recs.rejections:
        if rejection.ticker == ticker:
            lines.append(f"Analyst rejected {ticker}: {rejection.reason}")
    return lines


def _scanner_lines(candidates: CandidateSet, ticker: str) -> list[str]:
    candidate = next(
        (item for item in candidates.candidates if item.ticker == ticker), None
    )
    lines = [
        f"Scanner run: {explain(candidates.explanation)}",
        "Scanner filter trace: "
        f"universe_tickers={candidates.filter_trace.universe_size}; "
        f"evaluated_tickers={candidates.filter_trace.evaluated}; "
        f"dropped_tickers_by_filter={dict(candidates.filter_trace.dropped_by_filter)}",
    ]
    if candidate is not None:
        lines.append(_candidate_line(candidate))
    verdict = _verdict(candidates.filter_trace.verdicts, ticker)
    if verdict is not None:
        lines.append(
            f"Scanner verdict for {ticker}: decision={verdict.decision}; "
            f"filter_fired={verdict.filter_fired}; bypassed={verdict.bypassed}; "
            f"skipped_filters={list(verdict.skipped_filters)}; "
            f"features={source_metric_map(verdict.features)}"
        )
    return lines


def _candidate_line(candidate: Candidate) -> str:
    return (
        f"Scanner candidate for {candidate.ticker}: rank_ordinal={candidate.rank}; "
        f"scanner_score={candidate.score:.3f}; "
        f"survived_filters={list(candidate.survived_filters)}; "
        f"skipped_filters={list(candidate.skipped_filters)}; "
        f"metrics={source_metric_map(candidate.metrics)}"
    )


def _recommendation(recs: RecommendationSet, ticker: str) -> Recommendation | None:
    return next((item for item in recs.recommendations if item.ticker == ticker), None)


def _verdict(items: tuple[FilterVerdict, ...], ticker: str) -> FilterVerdict | None:
    return next((item for item in items if item.ticker == ticker), None)


def _first(items: Iterable[Node]) -> Node | None:
    return next(iter(items), None)
