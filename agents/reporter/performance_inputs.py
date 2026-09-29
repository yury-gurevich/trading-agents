"""Date-bounded graph inputs for reporter performance.

Agent: reporter
Role: read execution snapshots and the run's own benchmark bars without mutation.
External I/O: GraphStore reads via the injected backend.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import TYPE_CHECKING

from agents.reporter.benchmark_input import run_benchmark
from agents.reporter.domain.performance import PerformancePoint, calculate_performance
from agents.reporter.snapshot_result import performance_headline_clause

if TYPE_CHECKING:
    from kernel import GraphStore, Node


@dataclass(frozen=True)
class PerformanceInputs:
    """Inputs and context needed to calculate one run's performance."""

    points: tuple[PerformancePoint, ...]
    benchmark_closes: dict[date, float]
    benchmark_ticker: str | None
    as_of: date


@dataclass(frozen=True)
class PerformanceProjection:
    """Calculated metrics and their operator-facing headline clause."""

    metrics: dict[str, float]
    headline_clause: str


def read_performance_inputs(
    graph: GraphStore, pm_run: Node, *, inception: date
) -> PerformanceInputs:
    """Read only performance facts known when the PM run was created."""
    cutoff = _utc_datetime(pm_run.props["created_at"])
    if cutoff is None:
        raise ValueError("PMRun.created_at must be an ISO-8601 timestamp")
    as_of = cutoff.date()
    points = _snapshot_points(graph, inception=inception, cutoff=cutoff)
    benchmark_closes, benchmark_ticker = run_benchmark(graph, pm_run, as_of=as_of)
    return PerformanceInputs(points, benchmark_closes, benchmark_ticker, as_of)


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


def _snapshot_points(
    graph: GraphStore, *, inception: date, cutoff: datetime
) -> tuple[PerformancePoint, ...]:
    # One point per UTC date: the latest fresh snapshot, the nearest to the close the
    # benchmark bar measures. Only snapshots created by the PM run's instant count, so
    # a re-report reproduces its figures (RPT-IDM-03). The earliest-per-date rule read
    # an intraday sync on a two-run day (work-queue 88, DL-224).
    latest: dict[date, tuple[datetime, PerformancePoint]] = {}
    for snapshot in graph.list_nodes("BrokerPositionSnapshot"):
        props = snapshot.props
        if props.get("status") != "fresh" or props.get("account_status") != "fresh":
            continue
        created_at = _utc_datetime(props.get("created_at"))
        if created_at is None or created_at > cutoff or created_at.date() < inception:
            continue
        equity_cents = props.get("account_equity_cents")
        if not isinstance(equity_cents, int):
            continue
        point = (
            created_at.date(),
            equity_cents,
            _long_value_cents(props.get("holdings")),
        )
        previous = latest.get(created_at.date())
        if previous is None or created_at > previous[0]:
            latest[created_at.date()] = (created_at, point)
    return tuple(
        point for _, point in sorted(latest.values(), key=lambda item: item[0])
    )


def _long_value_cents(holdings: object) -> int:
    if not isinstance(holdings, Sequence):
        return 0
    return sum(
        holding["market_value_cents"]
        for holding in holdings
        if isinstance(holding, Mapping)
        and isinstance(holding.get("market_value_cents"), int)
    )


def _utc_datetime(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return (
        parsed.replace(tzinfo=UTC) if parsed.tzinfo is None else parsed.astimezone(UTC)
    )


def _no_sessions_reason(inputs: PerformanceInputs) -> str:
    if not inputs.points:
        return "no fresh snapshots"
    if len(inputs.points) < 2:
        return "fewer than two fresh snapshots"
    if not inputs.benchmark_closes:
        return "missing benchmark"
    return "no benchmark-aligned sessions"
