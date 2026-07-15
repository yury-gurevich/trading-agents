"""Reporter response assembly helpers.

Agent: reporter
Role: build reporter contract payloads from graph traversal and store writes.
External I/O: GraphStore writes via the injected backend.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.reporter.domain.lineage import (
    collect_run_lineage,
    collect_trade_lineage,
    run_id,
    run_id_from_position_id,
)
from agents.reporter.domain.metrics import (
    collect_portfolio_metrics,
    collect_regime_attribution,
    collect_signal_metrics,
)
from agents.reporter.domain.narrative import compose_story
from agents.reporter.domain.trade_outcomes import collect_trade_outcomes
from agents.reporter.store import write_snapshot, write_trade_narrative
from contracts.common import Explanation
from contracts.reporter import RunSnapshot, TradeNarrative

if TYPE_CHECKING:
    from kernel import GraphStore, Node


def build_snapshot(graph: GraphStore, run_id: str) -> RunSnapshot:
    """Build and persist one run snapshot from the provenance graph."""
    pm_run = graph.get_node("PMRun", run_id)
    if pm_run is None:
        return degraded_snapshot(graph, run_id, f"No PMRun found for {run_id}.")
    lineage_run = _linked_pm_source(graph, pm_run)
    lineage = collect_run_lineage(graph, lineage_run)
    portfolio = collect_portfolio_metrics(
        pm_run, lineage.positions, lineage.close_decisions
    )
    outcomes = collect_trade_outcomes(lineage.close_decisions)
    portfolio = {**portfolio, **outcomes}
    signal = collect_signal_metrics(
        lineage.recommendations, rejection_count=len(lineage.rejections)
    )
    regime = collect_regime_attribution(lineage.scan_runs, lineage.market_snapshots)
    headline = _headline(portfolio, signal)
    provenance = write_snapshot(
        graph,
        run_id=run_id,
        metrics_blob={"portfolio": portfolio, "signal": signal, "regime": regime},
        headline_summary=headline.summary,
    )
    return RunSnapshot(
        run_id=run_id,
        portfolio_metrics=portfolio,
        signal_metrics=signal,
        regime_attribution=regime,
        headline=headline,
        provenance=provenance,
    )


def build_trade_narrative(
    graph: GraphStore, position_id: str, *, max_chars: int
) -> TradeNarrative:
    """Build and persist one trade narrative from the provenance graph."""
    position = graph.get_node("Position", position_id)
    if position is None:
        return degraded_narrative(graph, position_id, max_chars=max_chars)
    lineage = collect_trade_lineage(graph, position)
    story = compose_story(
        lineage.position,
        lineage.fill,
        lineage.order_intent,
        lineage.recommendation,
        lineage.candidate,
        lineage.scan_run,
        lineage.close_decision,
    )
    return _narrative_result(
        graph, run_id(position), position_id, _trim(story, max_chars)
    )


def degraded_snapshot(graph: GraphStore, run_id: str, message: str) -> RunSnapshot:
    """Build and persist a non-crashing degraded snapshot."""
    portfolio = collect_portfolio_metrics(None, (), ())
    portfolio = {**portfolio, **collect_trade_outcomes(())}
    signal = collect_signal_metrics(())
    headline = Explanation(summary=message, evidence_refs=("reporter.graph",))
    provenance = write_snapshot(
        graph,
        run_id=run_id,
        metrics_blob={"portfolio": portfolio, "signal": signal, "regime": {}},
        headline_summary=headline.summary,
    )
    return RunSnapshot(
        run_id=run_id,
        portfolio_metrics=portfolio,
        signal_metrics=signal,
        regime_attribution={},
        headline=headline,
        provenance=provenance,
    )


def degraded_narrative(
    graph: GraphStore, position_id: str, *, max_chars: int
) -> TradeNarrative:
    """Build and persist a non-crashing degraded narrative."""
    summary = f"No Position found for {position_id}; trade story data unavailable."
    return _narrative_result(
        graph,
        run_id_from_position_id(position_id),
        position_id,
        _trim(summary, max_chars),
    )


def _narrative_result(
    graph: GraphStore, run_id: str, position_id: str, summary: str
) -> TradeNarrative:
    provenance = write_trade_narrative(
        graph, run_id=run_id, position_id=position_id, story=summary
    )
    return TradeNarrative(
        position_id=position_id,
        story=Explanation(summary=summary, evidence_refs=("reporter.graph",)),
        provenance=provenance,
    )


def _headline(portfolio: dict[str, float], signal: dict[str, float]) -> Explanation:
    return Explanation(
        summary=(
            f"{portfolio['positions_opened']:.0f} positions opened; "
            f"{portfolio['positions_closed']:.0f} closed; "
            f"{signal['recommendation_count']:.0f} recommendations stitched."
        ),
        evidence_refs=("portfolio_manager", "execution", "monitor", "analyst"),
    )


def _trim(summary: str, max_chars: int) -> str:
    return summary if len(summary) <= max_chars else summary[:max_chars]


def _linked_pm_source(graph: GraphStore, pm_run: Node) -> Node:
    """Return immutable source evidence when a resumed PM artifact is linked."""
    key = pm_run.props.get("linked_from_key")
    source = graph.get_node("PMRun", str(key)) if key else None
    return source or pm_run
