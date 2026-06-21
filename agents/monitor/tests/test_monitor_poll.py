"""Monitor graph-poll find_pending + monitor_pm_node tests.

Agent: monitor
Role: verify the monitor finds unprocessed ExecutionRun nodes and evaluates the PM
      run's positions from the graph (fills via PMRun lineage + current prices from the
      same-cycle MarketData), marking each processed so it is not re-monitored.
External I/O: none.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from agents.monitor.poll import find_pending, monitor_pm_node
from agents.monitor.tests.helpers import bar, seed_fill
from contracts.common import Provenance
from contracts.provider import DataQualityTrace, MarketData
from kernel import InMemoryGraphStore

if TYPE_CHECKING:
    from kernel import Node

_PM_RUN = "pm-run-fixture"
_EXEC_RUN = "execution-submit-pm-run-fixture"


def _market(close: float) -> MarketData:
    return MarketData(
        bars=(bar("AAPL", 0, close),),
        quality=DataQualityTrace(requested=1, returned=1),
        provenance=Provenance(run_id="provider-md", source_agent="provider"),
    )


def _seed(
    graph: InMemoryGraphStore, *, close: float = 100.0, lineage: bool = True
) -> Node:
    seed_fill(graph, price_cents=int(close * 100))
    pm_run = graph.get_node("PMRun", _PM_RUN)
    assert pm_run is not None
    exec_run = graph.merge_node(
        "ExecutionRun", _EXEC_RUN, {"source_pm_run_id": _PM_RUN}
    )
    graph.add_edge(pm_run, exec_run, "EXECUTED_BY")
    if lineage:
        analyst = graph.merge_node("AnalystRun", "analyst-1", {})
        scan = graph.merge_node("ScanRun", "scan-1", {})
        graph.add_edge(analyst, pm_run, "EVALUATED_BY")
        graph.add_edge(scan, analyst, "ANALYZED_BY")
        market_node = graph.merge_node(
            "MarketData",
            "market-data:fixture",
            {"snapshot": _market(close).model_dump(mode="json")},
        )
        graph.add_edge(scan, market_node, "DERIVED_FROM")
    return exec_run


def test_find_pending_returns_unmonitored_execution_run() -> None:
    graph = InMemoryGraphStore()
    _seed(graph)
    assert len(find_pending(graph)) == 1


def test_find_pending_empty_when_no_execution_run() -> None:
    assert find_pending(InMemoryGraphStore()) == []


def test_monitor_pm_node_checks_positions_from_graph() -> None:
    graph = InMemoryGraphStore()
    node = _seed(graph)
    monitor_pm_node(node, graph=graph)
    runs = graph.list_nodes("MonitorRun")
    assert len(runs) == 1
    assert runs[0].props["positions_checked"] == 1
    assert find_pending(graph) == []


def test_monitor_pm_node_no_market_lineage_checks_nothing() -> None:
    graph = InMemoryGraphStore()
    node = _seed(graph, lineage=False)
    monitor_pm_node(node, graph=graph)
    runs = graph.list_nodes("MonitorRun")
    assert len(runs) == 1
    assert runs[0].props["positions_checked"] == 0
    assert find_pending(graph) == []


def test_monitor_pm_node_stamps_recent_run() -> None:
    graph = InMemoryGraphStore()
    node = _seed(graph)
    monitor_pm_node(node, graph=graph)
    run = graph.list_nodes("MonitorRun")[0]
    created = datetime.fromisoformat(str(run.props["created_at"]))
    assert created <= datetime.now(tz=UTC)
