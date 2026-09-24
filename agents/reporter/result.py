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
    linked_pm_source,
    run_id,
)
from agents.reporter.domain.metrics import (
    collect_portfolio_metrics,
    collect_regime_attribution,
    collect_signal_metrics,
)
from agents.reporter.domain.narrative import compose_story
from agents.reporter.domain.trade_outcomes import collect_trade_outcomes
from agents.reporter.narrative_result import (
    degraded_narrative,
    narrative_result,
    trim_summary,
)
from agents.reporter.performance_inputs import (
    degraded_performance,
    performance_projection,
)
from agents.reporter.settings import ReporterSettings
from agents.reporter.snapshot_result import snapshot_headline
from agents.reporter.store import write_snapshot
from contracts.common import Explanation
from contracts.reporter import RunSnapshot, TradeNarrative
from kernel import CollectingFaultSink
from kernel.errors import fault_boundary

if TYPE_CHECKING:
    from kernel import FaultSink, GraphStore


def build_snapshot(
    graph: GraphStore,
    run_id: str,
    *,
    settings: ReporterSettings | None = None,
    sink: FaultSink | None = None,
) -> RunSnapshot:
    """Build and persist one run snapshot from the provenance graph."""
    pm_run = graph.get_node("PMRun", run_id)
    if pm_run is None:
        return degraded_snapshot(graph, run_id, f"No PMRun found for {run_id}.")
    settings = settings or ReporterSettings()
    lineage_run = linked_pm_source(graph, pm_run)
    lineage = collect_run_lineage(graph, lineage_run)
    portfolio = collect_portfolio_metrics(
        pm_run, lineage.positions, lineage.close_decisions, lineage.fills
    )
    outcomes = collect_trade_outcomes(lineage.fills, lineage.close_decisions)
    portfolio = {**portfolio, **outcomes}
    signal = collect_signal_metrics(
        lineage.recommendations, rejection_count=len(lineage.rejections)
    )
    regime = collect_regime_attribution(lineage.scan_runs, lineage.market_snapshots)
    performance = degraded_performance(
        inception=settings.performance_inception,
        rolling_sessions=settings.performance_rolling_sessions,
        reason="performance inputs unavailable",
    )
    with fault_boundary(
        sink or CollectingFaultSink(),
        agent="reporter",
        module="agents.reporter.result",
        capability="report.performance",
        reraise=False,
    ):
        performance = performance_projection(
            graph,
            pm_run,
            inception=settings.performance_inception,
            rolling_sessions=settings.performance_rolling_sessions,
        )
    headline = snapshot_headline(portfolio, signal, performance.headline_clause)
    provenance = write_snapshot(
        graph,
        run_id=run_id,
        metrics_blob={
            "portfolio": portfolio,
            "signal": signal,
            "regime": regime,
            "performance": performance.metrics,
        },
        headline_summary=headline.summary,
    )
    return RunSnapshot(
        run_id=run_id,
        portfolio_metrics=portfolio,
        signal_metrics=signal,
        regime_attribution=regime,
        performance_metrics=performance.metrics,
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
    return narrative_result(
        graph,
        run_id=run_id(position),
        position_id=position_id,
        summary=trim_summary(story, max_chars),
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
