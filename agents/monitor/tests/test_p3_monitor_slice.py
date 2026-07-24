"""Full P3 monitor lineage integration test.

Agent: monitor
Role: verify scanner→analyst→PM→execution→monitor stop-observation lineage.
External I/O: none.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from agents.analyst import AnalystAgent
from agents.execution import ExecutionAgent
from agents.execution.broker import PaperBroker
from agents.monitor import MonitorAgent
from agents.monitor.tests.helpers import (
    analysis_message,
    bar,
    monitor_message,
    orders_message,
    pipeline_entry_bars,
    scan_message,
    submit_message,
)
from agents.portfolio_manager import PortfolioManagerAgent
from agents.portfolio_manager.settings import PortfolioManagerSettings
from agents.provider import ProviderAgent
from agents.provider.settings import ProviderSettings
from agents.provider.sources import FakeDataSource
from agents.scanner import ScannerAgent
from agents.scanner.settings import ScannerSettings
from agents.scanner.universe import FakeUniverse
from contracts.analyst import RecommendationSet
from contracts.monitor import CloseDecisionSet
from contracts.portfolio_manager import OrderIntentSet
from contracts.scanner import CandidateSet
from kernel import InMemoryGraphStore, InProcessBus

if TYPE_CHECKING:
    from collections.abc import Iterable

    from contracts.provider import OHLCVBar
    from kernel import Node


def test_full_p3_slice_records_stop_check_fault_without_dispatch() -> None:
    bus = InProcessBus()
    graph = InMemoryGraphStore()
    broker = PaperBroker()
    _bind_pipeline(bus, graph, broker, pipeline_entry_bars())

    scan = bus.request(scan_message())
    analysis = bus.request(analysis_message(CandidateSet.model_validate(scan.payload)))
    orders = bus.request(
        orders_message(RecommendationSet.model_validate(analysis.payload))
    )
    execution = bus.request(
        submit_message(OrderIntentSet.model_validate(orders.payload))
    )
    _bind_provider(bus, graph, (bar("AAPL", 0, 100.0),))
    monitor = bus.request(monitor_message(str(orders.payload["run_id"])))

    result = CloseDecisionSet.model_validate(monitor.payload)
    check = _only_check(graph)
    assert scan.message_type == "response"
    assert analysis.message_type == "response"
    assert orders.message_type == "response"
    assert execution.message_type == "response"
    assert monitor.message_type == "response"
    assert result.decisions == ()
    assert result.positions_checked == 1
    assert broker.order_count == 1
    assert graph.list_nodes("CloseDecision") == ()
    assert graph.list_nodes("Fault")[0].props["message"] == (
        "stop breached on AAPL, still held"
    )
    _assert_lineage(graph, check)


def _bind_pipeline(
    bus: InProcessBus,
    graph: InMemoryGraphStore,
    broker: PaperBroker,
    bars: tuple[OHLCVBar, ...],
) -> None:
    _bind_provider(bus, graph, bars)
    ScannerAgent(
        bus,
        graph=graph,
        universe=FakeUniverse({"fixture": ("AAPL", "MSFT")}),
        settings=ScannerSettings(
            min_relative_strength=0.02,
            min_price=5.0,
            min_average_volume=500_000.0,
            candidate_cap=1,
            lookback_days=7,
        ),
    ).bind()
    AnalystAgent(bus, graph=graph).bind()
    PortfolioManagerAgent(
        bus,
        graph=graph,
        settings=PortfolioManagerSettings(starting_cash=Decimal("10000.00")),
    ).bind()
    ExecutionAgent(bus, graph=graph, broker=broker).bind()
    MonitorAgent(bus, graph=graph).bind()


def _bind_provider(
    bus: InProcessBus, graph: InMemoryGraphStore, bars: tuple[OHLCVBar, ...]
) -> None:
    ProviderAgent(
        bus,
        graph=graph,
        source=FakeDataSource(bars=bars, vix=12.0),
        settings=ProviderSettings(max_staleness_days=7),
    ).bind()


def _assert_lineage(graph: InMemoryGraphStore, check: Node) -> None:
    position = _only(graph.descendants(check, max_depth=1, edge_types={"CHECKS"}))
    fill = _only(graph.ancestors(position, max_depth=1, edge_types={"OPENS"}))
    order = _only(graph.descendants(fill, max_depth=1, edge_types={"EXECUTES"}))
    recommendation = _only(
        graph.descendants(order, max_depth=1, edge_types={"APPROVES"})
    )
    candidate = _only(
        graph.descendants(recommendation, max_depth=1, edge_types={"DERIVED_FROM"})
    )
    scan = _only(graph.descendants(candidate, max_depth=1, edge_types={"SURVIVED"}))
    snapshot = _only(graph.descendants(scan, max_depth=1, edge_types={"DERIVED_FROM"}))
    lineage = (check, position, fill, order, recommendation, candidate, scan, snapshot)
    assert [node.label for node in lineage] == [
        "PositionCheck",
        "Position",
        "Fill",
        "OrderIntent",
        "Recommendation",
        "Candidate",
        "ScanRun",
        "MarketSnapshot",
    ]


def _only_check(graph: InMemoryGraphStore) -> Node:
    rows = graph.list_nodes("PositionCheck")
    assert len(rows) == 1
    return rows[0]


def _only(nodes: Iterable[Node]) -> Node:
    rows = tuple(nodes)
    assert len(rows) == 1
    return rows[0]
