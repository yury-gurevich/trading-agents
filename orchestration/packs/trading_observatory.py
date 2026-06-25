"""Trading-pipeline invariants for the observatory (pack, not substrate).

Agent: orchestration
Role: extract the observable values from each stage of a trading run (provider ->
      pm) and declare the floor/ceiling/required invariants that say a run is
      healthy — the trading PACK of the domain-agnostic observatory. These are the
      "what must be there" + "floor/ceiling" locks for the trade pipeline; the
      mechanism that evaluates and renders them is substrate (observatory.py).
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

    quality = MarketData.model_validate(node.props["snapshot"]).quality
    ratio = round(quality.returned / max(quality.requested, 1), 3)
    observed: dict[str, object] = {
        "requested": quality.requested,
        "returned": quality.returned,
        "return_ratio": ratio,
        "degraded": quality.used_fallback,
        "stale": len(quality.stale_tickers),
    }
    checks = (Check("returned", "floor", 1.0), Check("return_ratio", "floor", 0.9))
    return StageView("provider", "RunRequest", observed, reached=True, checks=checks)


def _scanner(graph: GraphStore, node: Node) -> StageView:
    del graph
    from contracts.scanner import CandidateSet

    candidate_set = CandidateSet.model_validate(node.props["candidate_set"])
    trace = candidate_set.filter_trace
    observed: dict[str, object] = {
        "universe": trace.universe_size,
        "evaluated": trace.evaluated,
        "survived": len(candidate_set.candidates),
    }
    checks = (Check("universe", "floor", 1.0), Check("evaluated", "floor", 1.0))
    return StageView(
        "scanner", "MarketData(provider)", observed, reached=True, checks=checks
    )


def _analyst(graph: GraphStore, node: Node) -> StageView:
    del graph
    from contracts.analyst import RecommendationSet

    rec_set = RecommendationSet.model_validate(node.props["recommendation_set"])
    observed: dict[str, object] = {
        "scored": len(rec_set.recommendations),
        "rejected": len(rec_set.rejections),
    }
    checks = (Check("scored", "floor", 1.0),)
    return StageView(
        "analyst", "CandidateSet(scanner)", observed, reached=True, checks=checks
    )


def _pm(graph: GraphStore, node: Node) -> StageView:
    del graph
    from contracts.portfolio_manager import OrderIntentSet

    intents = OrderIntentSet.model_validate(node.props["order_intent_set"])
    evaluated = len(intents.approved) + len(intents.rejected)
    observed: dict[str, object] = {
        "approved": len(intents.approved),
        "rejected": len(intents.rejected),
        "evaluated": evaluated,
    }
    checks = (Check("evaluated", "floor", 1.0),)
    return StageView(
        "pm", "RecommendationSet(analyst)", observed, reached=True, checks=checks
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
