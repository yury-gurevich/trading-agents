"""Trading-pipeline invariants for the observatory (pack, not substrate).

Agent: orchestration
Role: extract each stage's OUTPUT artifacts (the tickers, scores, recommendations,
      orders a human wants to see) and the floor/ceiling/required invariants that
      say a run is healthy — the trading PACK of the domain-agnostic observatory.
      The mechanism that evaluates and renders is substrate (observatory.py).
External I/O: none (reads the injected GraphStore via walk_chain).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from orchestration.batch_trace import walk_chain
from orchestration.observatory import Check, StageView, render

if TYPE_CHECKING:
    from kernel import GraphStore, Node


def _provider(graph: GraphStore, node: Node) -> StageView:
    del graph
    from contracts.provider import MarketData

    market = MarketData.model_validate(node.props["snapshot"])
    quality = market.quality
    ratio = round(quality.returned / max(quality.requested, 1), 3)
    bars: dict[str, int] = {}
    for one in market.bars:
        bars[one.ticker] = bars.get(one.ticker, 0) + 1
    flag = "DEGRADED" if quality.used_fallback else "ok"
    outputs: tuple[str, ...] = (
        f"tickers   {' '.join(node.props['tickers'])}",
        "bars      " + "  ".join(f"{t}:{n}" for t, n in sorted(bars.items())),
        f"quality   {flag}  returned={quality.returned}/{quality.requested}",
    )
    if quality.stale_tickers:
        outputs += (f"stale     {' '.join(quality.stale_tickers)}",)
    observed: dict[str, object] = {"returned": quality.returned, "return_ratio": ratio}
    checks = (Check("returned", "floor", 1.0), Check("return_ratio", "floor", 0.9))
    return StageView(
        "provider", "RunRequest", observed, reached=True, checks=checks, outputs=outputs
    )


def _scanner(graph: GraphStore, node: Node) -> StageView:
    del graph
    from contracts.scanner import CandidateSet

    candidate_set = CandidateSet.model_validate(node.props["candidate_set"])
    trace = candidate_set.filter_trace
    ranked = sorted(candidate_set.candidates, key=lambda c: -c.score)
    outputs = (
        f"universe={trace.universe_size}  evaluated={trace.evaluated}"
        f"  survived={len(candidate_set.candidates)}",
        "scores    " + "  ".join(f"{c.ticker}:{c.score:.1f}" for c in ranked),
    )
    observed: dict[str, object] = {
        "universe": trace.universe_size,
        "evaluated": trace.evaluated,
    }
    checks = (Check("universe", "floor", 1.0), Check("evaluated", "floor", 1.0))
    return StageView(
        "scanner",
        "MarketData(provider)",
        observed,
        reached=True,
        checks=checks,
        outputs=outputs,
    )


def _analyst(graph: GraphStore, node: Node) -> StageView:
    del graph
    from contracts.analyst import RecommendationSet

    rec_set = RecommendationSet.model_validate(node.props["recommendation_set"])
    ranked = sorted(rec_set.recommendations, key=lambda r: -r.confidence)
    outputs: tuple[str, ...] = (
        f"scored={len(rec_set.recommendations)}  rejected={len(rec_set.rejections)}",
    )
    outputs += tuple(
        f"{r.ticker:<6} {r.action} conf={r.confidence:.2f} tech={r.technical_score:.1f}"
        for r in ranked
    )
    outputs += tuple(f"{r.ticker:<6} REJECT  {r.reason}" for r in rec_set.rejections)
    observed: dict[str, object] = {"scored": len(rec_set.recommendations)}
    checks = (Check("scored", "floor", 1.0),)
    return StageView(
        "analyst",
        "CandidateSet(scanner)",
        observed,
        reached=True,
        checks=checks,
        outputs=outputs,
    )


def _pm(graph: GraphStore, node: Node) -> StageView:
    del graph
    from contracts.portfolio_manager import OrderIntentSet

    intents = OrderIntentSet.model_validate(node.props["order_intent_set"])
    evaluated = len(intents.approved) + len(intents.rejected)
    outputs: tuple[str, ...] = (
        f"approved={len(intents.approved)}  rejected={len(intents.rejected)}",
    )
    outputs += tuple(
        f"{o.ticker:<6} {o.action}  qty={o.quantity}  est=${o.est_price.amount:.2f}"
        for o in intents.approved
    )
    outputs += tuple(f"{o.ticker:<6} SKIP  {o.reason}" for o in intents.rejected)
    observed: dict[str, object] = {"evaluated": evaluated}
    checks = (Check("evaluated", "floor", 1.0),)
    return StageView(
        "pm",
        "RecommendationSet(analyst)",
        observed,
        reached=True,
        checks=checks,
        outputs=outputs,
    )


# (stage name, graph label, trigger label, extractor). Order = the trade spine.
_SPEC = (
    ("provider", "MarketData", "RunRequest", _provider),
    ("scanner", "ScanRun", "MarketData(provider)", _scanner),
    ("analyst", "AnalystRun", "CandidateSet(scanner)", _analyst),
    ("pm", "PMRun", "RecommendationSet(analyst)", _pm),
)


def observe_run(graph: GraphStore, run_id: str) -> tuple[StageView, ...]:
    """Build the per-stage views for one run — unreached stages flagged, not dropped."""
    nodes = walk_chain(graph, run_id)
    views: list[StageView] = []
    for name, label, trigger, extractor in _SPEC:
        node = nodes.get(label)
        if node is None:
            views.append(StageView(name, trigger, {}, reached=False))
        else:
            views.append(extractor(graph, node))
    return tuple(views)


def inspect(graph: GraphStore, run_id: str) -> str:
    """Observe one run and render the observatory print."""
    return render(observe_run(graph, run_id))
