"""Graph reads for a run's book metrics.

Agent: reporter
Role: read Fills and PMRuns once and project the run's window and outcomes.
External I/O: GraphStore reads via the injected backend.
"""

from __future__ import annotations

from datetime import UTC, datetime, time
from typing import TYPE_CHECKING

from agents.reporter.domain.book_window import (
    book_counts,
    exits_since,
    filled_fills,
    fills_between,
    utc_instant,
    window_start,
)
from agents.reporter.domain.trade_outcomes import collect_trade_outcomes
from kernel.errors import fault_boundary

if TYPE_CHECKING:
    from datetime import date

    from kernel import FaultSink, GraphStore, Node


def book_metrics(
    graph: GraphStore, pm_run: Node, *, inception: date, sink: FaultSink
) -> dict[str, float]:
    """Return the run's book metrics; a failure leaves them absent and is a fault."""
    with fault_boundary(
        sink,
        agent="reporter",
        module="agents.reporter.book_inputs",
        capability="report.book",
        reraise=False,
    ) as capture:
        metrics = read_book_metrics(graph, pm_run, inception=inception)
    return {} if capture.fault is not None else metrics


def read_book_metrics(
    graph: GraphStore, pm_run: Node, *, inception: date
) -> dict[str, float]:
    """Count the run's window and the exits since the inception (RPT-OUT-02).

    Nothing refreshed after `PMRun.created_at` is read, and the window starts at
    another PMRun's `created_at`, so a re-report reproduces them (RPT-IDM-04). A run
    with no readable `created_at` has no window: the keys are absent (RPT-NEV-03).
    """
    reported_at = utc_instant(pm_run.props.get("created_at"))
    if reported_at is None:
        return {}
    timed = filled_fills(graph.list_nodes("Fill"))
    after = window_start(graph.list_nodes("PMRun"), reported_at)
    since = datetime.combine(inception, time.min, tzinfo=UTC)
    return {
        **book_counts(fills_between(timed, after, reported_at)),
        **collect_trade_outcomes(exits_since(timed, since, reported_at)),
    }
