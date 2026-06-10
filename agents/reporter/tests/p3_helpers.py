"""Reporter P3 integration helpers.

Agent: reporter
Role: wire the seven-agent in-process pipeline for reporter P3 tests.
External I/O: none.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from agents.analyst import AnalystAgent
from agents.execution import ExecutionAgent
from agents.monitor import MonitorAgent
from agents.portfolio_manager import PortfolioManagerAgent
from agents.portfolio_manager.settings import PortfolioManagerSettings
from agents.provider import ProviderAgent
from agents.provider.settings import ProviderSettings
from agents.provider.sources import FakeDataSource
from agents.reporter import ReporterAgent
from agents.reporter.tests.helpers import bar
from agents.scanner import ScannerAgent
from agents.scanner.settings import ScannerSettings
from agents.scanner.universe import FakeUniverse
from kernel import AgentMessage, InMemoryGraphStore, InProcessBus

if TYPE_CHECKING:
    from collections.abc import Iterable

    from agents.execution.broker import PaperBroker
    from contracts.analyst import RecommendationSet
    from contracts.portfolio_manager import OrderIntentSet
    from contracts.provider import OHLCVBar
    from contracts.scanner import CandidateSet
    from kernel import Node


def bind_pipeline(
    bus: InProcessBus,
    graph: InMemoryGraphStore,
    broker: PaperBroker,
    bars: tuple[OHLCVBar, ...],
) -> None:
    """Bind all seven P3 agents on one bus."""
    bind_provider(bus, graph, bars)
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
    ReporterAgent(bus, graph=graph).bind()


def bind_provider(
    bus: InProcessBus, graph: InMemoryGraphStore, bars: tuple[OHLCVBar, ...]
) -> None:
    """Bind or rebind the provider with a deterministic source."""
    ProviderAgent(
        bus,
        graph=graph,
        source=FakeDataSource(bars=bars, vix=12.0),
        settings=ProviderSettings(max_staleness_days=7),
    ).bind()


def entry_bars() -> tuple[OHLCVBar, ...]:
    """Return scan/analyze/PM bars that approve one AAPL order."""
    return (
        bar("AAPL", 6, 100.0),
        bar("AAPL", 4, 104.0),
        bar("AAPL", 2, 108.0),
        bar("AAPL", 0, 116.0),
        bar("MSFT", 6, 100.0),
        bar("MSFT", 0, 110.0),
    )


def scan_message() -> AgentMessage:
    """Build a scanner request for the P3 fixture universe."""
    return AgentMessage(
        sender="tester",
        recipient="scanner",
        message_type="request",
        capability="run_scan",
        payload={"run_id": "p3-reporter-test", "universe": "fixture"},
    )


def analysis_message(payload: CandidateSet) -> AgentMessage:
    """Build an analyst request."""
    return AgentMessage(
        sender="tester",
        recipient="analyst",
        message_type="request",
        capability="analyze",
        payload=payload.model_dump(mode="json"),
    )


def orders_message(payload: RecommendationSet) -> AgentMessage:
    """Build a PM request."""
    return AgentMessage(
        sender="tester",
        recipient="portfolio_manager",
        message_type="request",
        capability="evaluate_orders",
        payload=payload.model_dump(mode="json"),
    )


def submit_message(payload: OrderIntentSet) -> AgentMessage:
    """Build an execution submit request."""
    return AgentMessage(
        sender="tester",
        recipient="execution",
        message_type="request",
        capability="submit",
        payload=payload.model_dump(mode="json"),
    )


def monitor_message(run_id: str) -> AgentMessage:
    """Build a monitor request."""
    return AgentMessage(
        sender="tester",
        recipient="monitor",
        message_type="request",
        capability="check_positions",
        payload={"run_id": run_id},
    )


def assert_reporter_outputs(graph: InMemoryGraphStore, run_id: str) -> None:
    """Assert reporter-owned graph nodes were written."""
    assert graph.get_node("Snapshot", f"snapshot:{run_id}") is not None
    assert graph.get_node("TradeNarrative", f"narrative:{run_id}:AAPL") is not None


def assert_complete_chain(graph: InMemoryGraphStore) -> None:
    """Assert the reporter story still reaches the market snapshot."""
    narrative = _only_label(graph, "TradeNarrative")
    position = _only(graph.descendants(narrative, max_depth=1, edge_types={"NARRATES"}))
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
    assert [
        node.label for node in (fill, order, recommendation, candidate, scan, snapshot)
    ] == [
        "Fill",
        "OrderIntent",
        "Recommendation",
        "Candidate",
        "ScanRun",
        "MarketSnapshot",
    ]


def _only_label(graph: InMemoryGraphStore, label: str) -> Node:
    rows = [
        node for (node_label, _key), node in graph._nodes.items() if node_label == label
    ]
    assert len(rows) == 1
    return rows[0]


def _only(nodes: Iterable[Node]) -> Node:
    rows = tuple(nodes)
    assert len(rows) == 1
    return rows[0]
