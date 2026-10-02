"""Date-bounded graph inputs for reporter performance.

Agent: reporter
Role: read execution snapshots and the run's own benchmark bars without mutation.
External I/O: GraphStore reads via the injected backend.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING

from agents.reporter.benchmark_input import run_benchmark
from agents.reporter.domain.book_window import utc_instant
from agents.reporter.domain.performance import PerformancePoint, calculate_performance
from agents.reporter.snapshot_result import performance_headline_clause

if TYPE_CHECKING:
    from datetime import date, datetime

    from kernel import GraphStore, Node


@dataclass(frozen=True)
class PerformanceInputs:
    """Inputs and context needed to calculate one run's performance."""

    points: tuple[PerformancePoint, ...]
    benchmark_closes: dict[date, float]
    benchmark_ticker: str | None
    as_of: date
    positions_held: float | None = None


@dataclass(frozen=True)
class PerformanceProjection:
    """Calculated metrics and their operator-facing headline clause."""

    metrics: dict[str, float]
    headline_clause: str
    positions_held: float | None = None


def read_performance_inputs(
    graph: GraphStore, pm_run: Node, *, inception: date
) -> PerformanceInputs:
    """Read only performance facts known when the PM run was created."""
    cutoff = utc_instant(pm_run.props["created_at"])
    if cutoff is None:
        raise ValueError("PMRun.created_at must be an ISO-8601 timestamp")
    as_of = cutoff.date()
    chosen = _as_of_snapshots(graph, inception=inception, cutoff=cutoff)
    points = tuple(_point(at, snapshot) for at, snapshot in chosen)
    benchmark_closes, benchmark_ticker = run_benchmark(graph, pm_run, as_of=as_of)
    held = _holding_count(chosen[-1][1]) if chosen else None
    return PerformanceInputs(points, benchmark_closes, benchmark_ticker, as_of, held)


def performance_projection(
    graph: GraphStore,
    pm_run: Node,
    *,
    inception: date,
    rolling_sessions: int,
) -> PerformanceProjection:
    """Read graph facts and calculate the bounded performance projection."""
    inputs = read_performance_inputs(graph, pm_run, inception=inception)
    metrics = calculate_performance(
        inputs.points, inputs.benchmark_closes, rolling_sessions=rolling_sessions
    )
    return PerformanceProjection(
        metrics=metrics,
        headline_clause=performance_headline_clause(
            metrics, inputs.benchmark_ticker, inception, _no_sessions_reason(inputs)
        ),
        positions_held=inputs.positions_held,
    )


def degraded_performance(
    *, inception: date, rolling_sessions: int, reason: str
) -> PerformanceProjection:
    """Return explicit zero metrics when performance input collection faults."""
    metrics = calculate_performance((), {}, rolling_sessions=rolling_sessions)
    return PerformanceProjection(
        metrics=metrics,
        headline_clause=performance_headline_clause(metrics, None, inception, reason),
    )


def _as_of_snapshots(
    graph: GraphStore, *, inception: date, cutoff: datetime
) -> tuple[tuple[datetime, Node], ...]:
    # One snapshot per UTC date: the latest fresh one, the nearest to the close the
    # benchmark bar measures. Only snapshots created by the PM run's instant count, so
    # a re-report reproduces its figures (RPT-IDM-03). The earliest-per-date rule read
    # an intraday sync on a two-run day (work-queue 88, DL-224). The last one chosen
    # is the run's as-of book, whose holdings are `positions_held` (RPT-OUT-02).
    latest: dict[date, tuple[datetime, Node]] = {}
    for snapshot in graph.list_nodes("BrokerPositionSnapshot"):
        props = snapshot.props
        if props.get("status") != "fresh" or props.get("account_status") != "fresh":
            continue
        created_at = utc_instant(props.get("created_at"))
        if created_at is None or created_at > cutoff or created_at.date() < inception:
            continue
        if not isinstance(props.get("account_equity_cents"), int):
            continue
        previous = latest.get(created_at.date())
        if previous is None or created_at > previous[0]:
            latest[created_at.date()] = (created_at, snapshot)
    return tuple(sorted(latest.values(), key=lambda pair: pair[0]))


def _point(created_at: datetime, snapshot: Node) -> PerformancePoint:
    props = snapshot.props
    holdings = _long_value_cents(props.get("holdings"))
    return (created_at.date(), props["account_equity_cents"], holdings)


def _holding_count(snapshot: Node) -> float | None:
    holdings = snapshot.props.get("holdings")
    if not isinstance(holdings, Sequence) or isinstance(holdings, str):
        return None
    return float(len(holdings))


def _long_value_cents(holdings: object) -> int:
    if not isinstance(holdings, Sequence):
        return 0
    return sum(
        holding["market_value_cents"]
        for holding in holdings
        if isinstance(holding, Mapping)
        and isinstance(holding.get("market_value_cents"), int)
    )


def _no_sessions_reason(inputs: PerformanceInputs) -> str:
    if not inputs.points:
        return "no fresh snapshots"
    if len(inputs.points) < 2:
        return "fewer than two fresh snapshots"
    if not inputs.benchmark_closes:
        return "missing benchmark"
    return "no benchmark-aligned sessions"
