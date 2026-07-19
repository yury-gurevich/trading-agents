"""Fixtures for deliberation veto context tests.

Agent: orchestration
Role: build compact graph-lineage payloads for veto evidence-renderer tests.
External I/O: none.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from tests.veto_context_gate_fixtures import pm_gate_report
from tests.veto_context_provider_fixtures import market_data, prov, regime

from contracts.analyst import QuantMetric, Recommendation, RecommendationSet, Rejection
from contracts.common import Explanation, Money
from contracts.portfolio_manager import GateOutcome, OrderIntent, OrderIntentSet
from contracts.provider import REGIME_CONTEXT_LABEL
from contracts.scanner import Candidate, CandidateSet, FilterTrace, FilterVerdict

if TYPE_CHECKING:
    from kernel import InMemoryGraphStore, Node


def linked_graph(graph: InMemoryGraphStore, *, full: bool) -> Node:
    """Create PM lineage: MarketData <- ScanRun -> AnalystRun -> PMRun."""
    market = graph.merge_node(
        "MarketData", "market", {"run_id": "market", "snapshot": market_data(full)}
    )
    if full:
        graph.merge_node(
            REGIME_CONTEXT_LABEL,
            "regime-context:market",
            {"snapshot": regime()},
        )
    scan = graph.merge_node("ScanRun", "scan", {"candidate_set": candidates(full)})
    graph.add_edge(scan, market, "DERIVED_FROM")
    analyst = graph.merge_node(
        "AnalystRun", "analyst", {"recommendation_set": recs(full)}
    )
    graph.add_edge(scan, analyst, "ANALYZED_BY")
    pm = graph.merge_node("PMRun", "pm", {})
    graph.add_edge(analyst, pm, "EVALUATED_BY")
    return pm


def intent(
    *,
    stop: float | None = 0.03,
    target: float | None = 0.08,
    gates: tuple[GateOutcome, ...] | None = None,
) -> OrderIntent:
    """Return one PM-approved order intent."""
    return OrderIntent(
        ticker="AAPL",
        action="buy",
        quantity=7,
        est_price=Money(amount=Decimal("116.00")),
        stop_pct=stop,
        target_pct=target,
        rationale=Explanation(summary="PM sized by risk budget"),
        gate_report=pm_gate_report() if gates is None else gates,
    )


def order_set(item: OrderIntent, refs: tuple[str, ...] = ()) -> OrderIntentSet:
    """Return the PM envelope that carries the approved order."""
    return OrderIntentSet(
        run_id="pm",
        approved=(item,),
        rejected=(),
        explanation=Explanation(summary="PM approved one order", evidence_refs=refs),
        provenance=prov("portfolio_manager"),
    )


def recs(full: bool = True, *, include_aapl: bool = True) -> dict[str, object]:
    """Return an analyst payload with optional score fields when full."""
    rec = Recommendation(
        ticker="AAPL",
        action="buy",
        confidence=0.62,
        technical_score=0.75,
        sentiment_score=0.70 if full else None,
        fundamental_score=0.65 if full else None,
        suggested_stop_pct=0.03 if full else None,
        suggested_target_pct=0.08 if full else None,
        quant_metrics=(
            QuantMetric(name="composite_score", value=0.61),
            QuantMetric(name="history_bars", value=40.0),
            QuantMetric(name="relative_strength", value=0.08),
        )
        if full
        else (),
        rationale=Explanation(summary="trend and quality aligned"),
    )
    recommendations = (rec,) if include_aapl else ()
    ticker = "AAPL" if full else "MSFT"
    rejections = (Rejection(ticker=ticker, reason="duplicate exposure"),)
    return RecommendationSet(
        run_id="analyst",
        recommendations=recommendations,
        rejections=rejections,
        explanation=Explanation(summary="analyst scored the survivor"),
        provenance=prov("analyst"),
    ).model_dump(mode="json")


def candidates(full: bool = True) -> dict[str, object]:
    """Return scanner payload; sparse mode makes AAPL absent."""
    ticker = "AAPL" if full else "MSFT"
    return CandidateSet(
        run_id="scan",
        candidates=(
            Candidate(
                ticker=ticker,
                rank=1,
                score=0.81,
                survived_filters=("price", "volume"),
                metrics={"beta": 1.1, "return_5d": 0.08},
            ),
        ),
        filter_trace=FilterTrace(
            universe_size=2,
            evaluated=2,
            dropped_by_filter={"earnings": 1},
            verdicts=(
                FilterVerdict(
                    ticker=ticker,
                    decision="survived",
                    features={"beta": 1.1, "return_5d": 0.08},
                ),
            ),
        ),
        explanation=Explanation(summary="scanner kept strongest name"),
        provenance=prov("scanner"),
    ).model_dump(mode="json")
