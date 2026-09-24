"""Date-bounded graph inputs for reporter performance.

Agent: reporter
Role: read execution snapshots and provider benchmark bars without mutation.
External I/O: GraphStore reads via the injected backend.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import TYPE_CHECKING

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
    """Read only performance facts known on the PM run's UTC date."""
    as_of = _utc_date(pm_run.props["created_at"])
    points = _snapshot_points(graph, inception=inception, as_of=as_of)
    benchmark_closes, benchmark_ticker = _benchmark(graph, as_of=as_of)
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
    graph: GraphStore, *, inception: date, as_of: date
) -> tuple[PerformancePoint, ...]:
    earliest: dict[date, tuple[datetime, PerformancePoint]] = {}
    for snapshot in graph.list_nodes("BrokerPositionSnapshot"):
        props = snapshot.props
        if props.get("status") != "fresh" or props.get("account_status") != "fresh":
            continue
        created_at = _utc_datetime(props.get("created_at"))
        if created_at is None or not inception <= created_at.date() <= as_of:
            continue
        equity_cents = props.get("account_equity_cents")
        if not isinstance(equity_cents, int):
            continue
        point = (
            created_at.date(),
            equity_cents,
            _long_value_cents(props.get("holdings")),
        )
        previous = earliest.get(created_at.date())
        if previous is None or created_at < previous[0]:
            earliest[created_at.date()] = (created_at, point)
    return tuple(
        point for _, point in sorted(earliest.values(), key=lambda item: item[0])
    )


def _benchmark(
    graph: GraphStore, *, as_of: date
) -> tuple[dict[date, float], str | None]:
    eligible: list[tuple[date, Mapping[str, object]]] = []
    for market_data in graph.list_nodes("MarketData"):
        window_end = _date_only(market_data.props.get("window_end"))
        snapshot = market_data.props.get("snapshot")
        if (
            window_end is None
            or window_end > as_of
            or not isinstance(snapshot, Mapping)
        ):
            continue
        benchmark = snapshot.get("benchmark")
        if isinstance(benchmark, Sequence) and benchmark:
            eligible.append((window_end, snapshot))
    if not eligible:
        return {}, None
    _, snapshot = max(eligible, key=lambda item: item[0])
    benchmark = snapshot["benchmark"]
    assert isinstance(benchmark, Sequence)
    closes: dict[date, float] = {}
    ticker: str | None = None
    for bar in benchmark:
        if not isinstance(bar, Mapping):
            continue
        bar_date = _date_only(bar.get("bar_date"))
        close = bar.get("close")
        if bar_date is None or bar_date > as_of or not isinstance(close, int | float):
            continue
        closes[bar_date] = float(close)
        if ticker is None and isinstance(bar.get("ticker"), str):
            ticker = bar["ticker"]
    return closes, ticker


def _long_value_cents(holdings: object) -> int:
    if not isinstance(holdings, Sequence):
        return 0
    return sum(
        holding["market_value_cents"]
        for holding in holdings
        if isinstance(holding, Mapping)
        and isinstance(holding.get("market_value_cents"), int)
    )


def _utc_date(value: object) -> date:
    parsed = _utc_datetime(value)
    if parsed is None:
        raise ValueError("PMRun.created_at must be an ISO-8601 timestamp")
    return parsed.date()


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


def _date_only(value: object) -> date | None:
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def _no_sessions_reason(inputs: PerformanceInputs) -> str:
    if not inputs.points:
        return "no fresh snapshots"
    if len(inputs.points) < 2:
        return "fewer than two fresh snapshots"
    if not inputs.benchmark_closes:
        return "missing benchmark"
    return "no benchmark-aligned sessions"
