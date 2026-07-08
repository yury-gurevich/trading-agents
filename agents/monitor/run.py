"""Monitor evaluate core shared by the bus and graph-pull paths.

Agent: monitor
Role: open filled positions, evaluate exits against current prices, and persist the
      monitor run. Called by the bus handler (`_check_positions`) and the graph-pull
      poll path (`monitor_pm_node`) so both stay consistent (DL-08b).
External I/O: none (reads/writes the injected GraphStore).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from agents.monitor.decide import evaluate_one
from agents.monitor.domain.positions import position_from_fill
from agents.monitor.position_book import active_positions
from agents.monitor.reconcile import reconcile_positions_from_latest_snapshot
from agents.monitor.result import run_explanation
from agents.monitor.store import (
    fills_for_run,
    open_position,
    write_monitor_run,
)
from contracts.monitor import CloseDecision, CloseDecisionSet
from kernel.errors import fault_boundary

if TYPE_CHECKING:
    from agents.monitor.settings import MonitorSettings
    from kernel import FaultSink, GraphStore, Node


def open_run_positions(
    graph: GraphStore, settings: MonitorSettings, sink: FaultSink, *, source_run_id: str
) -> tuple[Node, ...]:
    """Open positions from a PM run's fills and return the not-yet-closed ones."""
    for fill in fills_for_run(graph, source_run_id):
        draft = position_from_fill(
            graph,
            run_id=source_run_id,
            fill=fill,
            default_stop_pct=settings.default_stop_pct,
            default_target_pct=settings.default_target_pct,
            default_horizon_days=settings.default_horizon_days,
        )
        if draft.degraded:
            _record_degraded(sink, "position opened with fallback stop/target")
        open_position(graph, draft, fill)
    reconcile_positions_from_latest_snapshot(graph, settings)
    return active_positions(graph)


def evaluate_and_write(
    graph: GraphStore,
    sink: FaultSink,
    *,
    source_run_id: str,
    positions: tuple[Node, ...],
    prices: dict[str, int] | None,
) -> CloseDecisionSet:
    """Evaluate exits against current prices and persist the monitor run."""
    monitor_run_id = f"monitor-run-{uuid.uuid4().hex}"
    decisions = (
        ()
        if prices is None
        else _evaluate_positions(graph, sink, monitor_run_id, positions, prices)
    )
    closes = tuple(item for item in decisions if item.decision == "close")
    provenance = write_monitor_run(
        graph,
        monitor_run_id=monitor_run_id,
        source_run_id=source_run_id,
        positions_checked=len(decisions),
        closes=len(closes),
        holds=len(decisions) - len(closes),
    )
    return CloseDecisionSet(
        run_id=monitor_run_id,
        decisions=decisions,
        positions_checked=len(decisions),
        explanation=run_explanation(decisions),
        provenance=provenance,
    )


def _evaluate_positions(
    graph: GraphStore,
    sink: FaultSink,
    monitor_run_id: str,
    positions: tuple[Node, ...],
    prices: dict[str, int],
) -> tuple[CloseDecision, ...]:
    decisions: list[CloseDecision] = []
    today = datetime.now(tz=UTC).date()
    for position in positions:
        ticker = str(position.props["ticker"])
        current_price_cents = prices.get(ticker)
        if current_price_cents is None:
            _record_degraded(sink, f"provider returned no current price for {ticker}")
            continue
        decisions.append(
            evaluate_one(graph, monitor_run_id, position, current_price_cents, today)
        )
    return tuple(decisions)


def _record_degraded(sink: FaultSink, message: str) -> None:
    """Record a degraded fault without interrupting the monitor run."""
    with fault_boundary(
        sink,
        agent="monitor",
        module="agents.monitor.run",
        capability="check_positions",
        reraise=False,
    ):
        raise RuntimeError(message)
