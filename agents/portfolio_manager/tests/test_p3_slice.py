"""Full P3 portfolio-manager lineage integration test.

Agent: portfolio_manager
Role: verify provider to scanner to analyst to PM provenance chain.
External I/O: none.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from agents.analyst import AnalystAgent
from agents.portfolio_manager import PortfolioManagerAgent
from agents.portfolio_manager.settings import PortfolioManagerSettings
from agents.portfolio_manager.tests.helpers import bar
from agents.provider import ProviderAgent
from agents.provider.settings import ProviderSettings
from agents.provider.sources import FakeDataSource
from agents.scanner import ScannerAgent
from agents.scanner.settings import ScannerSettings
from agents.scanner.universe import FakeUniverse
from contracts.analyst import RecommendationSet
from contracts.portfolio_manager import OrderIntentSet
from contracts.scanner import CandidateSet
from kernel import AgentMessage, InMemoryGraphStore, InProcessBus

if TYPE_CHECKING:
    from contracts.provider import OHLCVBar


def test_full_p3_slice_produces_order_intent_with_complete_lineage() -> None:
    bus = InProcessBus()
    graph = InMemoryGraphStore()
    ProviderAgent(
        bus,
        graph=graph,
        source=FakeDataSource(bars=_pipeline_bars(), vix=12.0),
        settings=ProviderSettings(max_staleness_days=7),
    ).bind()
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

    scan = bus.request(_scan_message())
    analysis = bus.request(_analysis_message(CandidateSet.model_validate(scan.payload)))
    orders = bus.request(
        _orders_message(RecommendationSet.model_validate(analysis.payload))
    )

    result = OrderIntentSet.model_validate(orders.payload)
    assert scan.message_type == "response"
    assert analysis.message_type == "response"
    assert orders.message_type == "response"
    assert [item.ticker for item in result.approved] == ["AAPL"]
    order = graph.get_node("OrderIntent", f"{result.run_id}:AAPL")
    assert order is not None
    recommendations = list(
        graph.descendants(order, max_depth=1, edge_types={"APPROVES"})
    )
    candidates = list(
        graph.descendants(recommendations[0], max_depth=1, edge_types={"DERIVED_FROM"})
    )
    scans = list(graph.descendants(candidates[0], max_depth=1, edge_types={"SURVIVED"}))
    snapshots = list(
        graph.descendants(scans[0], max_depth=1, edge_types={"DERIVED_FROM"})
    )
    assert [node.label for node in recommendations] == ["Recommendation"]
    assert [node.label for node in candidates] == ["Candidate"]
    assert [node.label for node in scans] == ["ScanRun"]
    assert [node.label for node in snapshots] == ["MarketSnapshot"]


def _pipeline_bars() -> tuple[OHLCVBar, ...]:
    return (
        bar("AAPL", 6, 100.0),
        bar("AAPL", 4, 104.0),
        bar("AAPL", 2, 108.0),
        bar("AAPL", 0, 116.0),
        bar("MSFT", 6, 100.0),
        bar("MSFT", 0, 110.0),
    )


def _scan_message() -> AgentMessage:
    return AgentMessage(
        sender="tester",
        recipient="scanner",
        message_type="request",
        capability="run_scan",
        payload={"run_id": "p3-test", "universe": "fixture"},
    )


def _analysis_message(payload: CandidateSet) -> AgentMessage:
    return AgentMessage(
        sender="tester",
        recipient="analyst",
        message_type="request",
        capability="analyze",
        payload=payload.model_dump(mode="json"),
    )


def _orders_message(payload: RecommendationSet) -> AgentMessage:
    return AgentMessage(
        sender="tester",
        recipient="portfolio_manager",
        message_type="request",
        capability="evaluate_orders",
        payload=payload.model_dump(mode="json"),
    )
