"""Reporter performance graph-input and containment tests.

Agent: reporter
Role: prove performance reads are bounded and snapshot failure is contained.
External I/O: none.
"""

from __future__ import annotations

from datetime import date

import pytest

from agents.reporter.performance_inputs import read_performance_inputs
from agents.reporter.result import build_snapshot
from agents.reporter.settings import ReporterSettings
from kernel import CollectingFaultSink, InMemoryGraphStore, Node


def test_performance_uses_earliest_fresh_snapshot_per_date() -> None:
    """RPT-OUT-07: daily performance point is the earliest fresh account snapshot."""
    graph = InMemoryGraphStore()
    pm_run = graph.merge_node("PMRun", "pm-run", {"created_at": "2026-08-11T22:30:00Z"})
    _snapshot(graph, "early", "2026-08-10T22:30:00Z", 1_000_000, status="fresh")
    _snapshot(graph, "late", "2026-08-10T22:44:00Z", 2_000_000, status="fresh")
    _snapshot(graph, "stale", "2026-08-10T22:20:00Z", 3_000_000, status="stale")

    inputs = read_performance_inputs(graph, pm_run, inception=date(2026, 8, 10))

    assert inputs.points == ((date(2026, 8, 10), 1_000_000, 500_000),)


def test_snapshot_names_no_fresh_snapshots_without_raising() -> None:
    """RPT-NEV-03: zero fresh points yields zero sessions and names the reason."""
    graph = InMemoryGraphStore()
    graph.merge_node("PMRun", "pm-run", {"created_at": "2026-08-10T22:30:00Z"})
    sink = CollectingFaultSink()

    snapshot = build_snapshot(graph, "pm-run", settings=_settings(), sink=sink)

    assert snapshot.performance_metrics["performance_sessions"] == 0.0
    assert "no fresh snapshots" in snapshot.headline.summary
    assert sink.faults == []


def test_snapshot_names_too_little_data_without_raising() -> None:
    """RPT-NEV-03: one fresh point yields zero sessions and names the reason."""
    graph = _performance_graph()
    sink = CollectingFaultSink()

    snapshot = build_snapshot(graph, "pm-run", settings=_settings(), sink=sink)

    assert snapshot.performance_metrics["performance_sessions"] == 0.0
    assert (
        "Performance: no usable sessions since 2026-08-10" in snapshot.headline.summary
    )
    assert "fewer than two fresh snapshots" in snapshot.headline.summary
    assert sink.faults == []


def test_snapshot_names_missing_benchmark_without_raising() -> None:
    """RPT-NEV-03: absent benchmark data yields zero sessions and names the reason."""
    graph = _performance_graph(as_of="2026-08-11T22:30:00Z")
    _snapshot(graph, "second", "2026-08-11T22:30:00Z", 1_010_000, status="fresh")
    sink = CollectingFaultSink()

    snapshot = build_snapshot(graph, "pm-run", settings=_settings(), sink=sink)

    assert snapshot.performance_metrics["performance_sessions"] == 0.0
    assert "missing benchmark" in snapshot.headline.summary
    assert sink.faults == []


def test_snapshot_contains_performance_fault_without_losing_other_groups() -> None:
    """RPT-FAIL-04: MarketData failure faults once and preserves groups."""
    graph = _MarketDataFailingGraph()
    graph.merge_node("PMRun", "pm-run", {"created_at": "2026-08-10T22:30:00Z"})
    _snapshot(graph, "first", "2026-08-10T22:30:00Z", 1_000_000, status="fresh")
    sink = CollectingFaultSink()

    snapshot = build_snapshot(graph, "pm-run", settings=_settings(), sink=sink)

    assert snapshot.portfolio_metrics["positions_opened"] == 0.0
    assert snapshot.signal_metrics["recommendation_count"] == 0.0
    assert snapshot.regime_attribution == {}
    assert snapshot.performance_metrics["performance_sessions"] == 0.0
    assert len(sink.faults) == 1


def test_snapshot_ignores_prior_reporter_performance_output() -> None:
    """RPT-ORD-01: report reads upstream facts, not prior reporter output."""
    graph = InMemoryGraphStore()
    graph.merge_node("PMRun", "pm-run", {"created_at": "2026-08-11T22:30:00Z"})
    _snapshot(graph, "first", "2026-08-10T22:30:00Z", 1_000_000, status="fresh")
    _snapshot(graph, "second", "2026-08-11T22:30:00Z", 1_100_000, status="fresh")
    graph.merge_node(
        "Snapshot",
        "snapshot:old",
        {"metrics": {"performance": {"portfolio_return_pct": 999.0}}},
    )
    graph.merge_node(
        "ReportSnapshotResult",
        "result:old",
        {"snapshot": {"performance_metrics": {"portfolio_return_pct": 999.0}}},
    )
    graph.merge_node(
        "MarketData",
        "market-data:pm-run",
        {
            "window_end": "2026-08-11",
            "snapshot": {
                "benchmark": [
                    {"ticker": "SPY", "bar_date": "2026-08-10", "close": 100.0},
                    {"ticker": "SPY", "bar_date": "2026-08-11", "close": 100.0},
                ]
            },
        },
    )

    snapshot = build_snapshot(graph, "pm-run", settings=_settings())

    assert snapshot.performance_metrics["portfolio_return_pct"] == pytest.approx(10.0)


def _performance_graph(*, as_of: str = "2026-08-10T22:30:00Z") -> InMemoryGraphStore:
    graph = InMemoryGraphStore()
    graph.merge_node("PMRun", "pm-run", {"created_at": as_of})
    _snapshot(graph, "first", "2026-08-10T22:30:00Z", 1_000_000, status="fresh")
    return graph


def _snapshot(
    graph: InMemoryGraphStore,
    key: str,
    created_at: str,
    equity_cents: int,
    *,
    status: str,
) -> None:
    graph.merge_node(
        "BrokerPositionSnapshot",
        key,
        {
            "status": status,
            "account_status": "fresh",
            "created_at": created_at,
            "account_equity_cents": equity_cents,
            "holdings": [{"market_value_cents": 500_000}],
        },
    )


def _settings() -> ReporterSettings:
    return ReporterSettings(
        performance_inception=date(2026, 8, 10), performance_rolling_sessions=20
    )


class _MarketDataFailingGraph(InMemoryGraphStore):
    def list_nodes(self, label: str) -> tuple[Node, ...]:
        if label == "MarketData":
            raise RuntimeError("market data unavailable")
        return super().list_nodes(label)
