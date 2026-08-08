"""Decision-chain stage view extractors for the graph observatory.

Agent: orchestration
Role: extract the scanner -> analyst -> PM selection stages, where each stage
      consumes the previous stage's artifact.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from orchestration.observatory import Check
from orchestration.packs.trading_stage_view import view
from orchestration.pm_rejections import format_pm_rejection

if TYPE_CHECKING:
    from kernel import GraphStore, Node
    from orchestration.observatory import StageView


def scanner(graph: GraphStore, node: Node) -> StageView:
    """Render scanner filter counts."""
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
        "survived": len(candidate_set.candidates),
    }
    checks = (Check("universe", "floor", 1.0), Check("evaluated", "floor", 1.0))
    return view("scanner", "MarketData(provider)", observed, checks, outputs)


def analyst(graph: GraphStore, node: Node) -> StageView:
    """Render analyst recommendations."""
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
    held = int(node.props.get("held_count", 0))
    observed: dict[str, object] = {"scored": len(rec_set.recommendations), "held": held}
    observed["rejected"] = len(rec_set.rejections)
    checks = (Check("scored", "floor", 1.0),)
    return view("analyst", "CandidateSet(scanner)", observed, checks, outputs)


def pm(graph: GraphStore, node: Node) -> StageView:
    """Render PM approvals and rejections."""
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
    outputs += tuple(format_pm_rejection(item) for item in intents.rejected)
    observed: dict[str, object] = {
        "approved": len(intents.approved),
        "evaluated": evaluated,
    }
    checks = (Check("evaluated", "floor", 1.0),)
    return view("pm", "RecommendationSet(analyst)", observed, checks, outputs)
