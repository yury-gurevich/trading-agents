"""Full P3 execution lineage integration test.

Agent: execution
Role: verify provider to scanner to analyst to PM to execution provenance chain.
External I/O: none.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from agents.analyst import AnalystAgent
from agents.execution import ExecutionAgent
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
from contracts.execution import ExecutionResult
from contracts.portfolio_manager import OrderIntentSet
from contracts.scanner import CandidateSet
from kernel import AgentMessage, InMemoryGraphStore, InProcessBus

if TYPE_CHECKING:
    from collections.abc import Iterable

    from contracts.provider import OHLCVBar
    from kernel import Node


def test_full_p3_slice_records_fill_with_complete_lineage() -> None:
    bus = InProcessBus()
    graph = InMemoryGraphStore()
    _bind_pipeline(bus, graph)

    scan = bus.request(_scan_message())
    analysis = bus.request(_analysis_message(CandidateSet.model_validate(scan.payload)))
    orders = bus.request(
        _orders_message(RecommendationSet.model_validate(analysis.payload))
    )
    execution = bus.request(
        _submit_message(OrderIntentSet.model_validate(orders.payload))
    )

    result = ExecutionResult.model_validate(execution.payload)
    fill = graph.get_node("Fill", f"{orders.payload['run_id']}:AAPL:buy")
    assert scan.message_type == "response"
    assert analysis.message_type == "response"
    assert orders.message_type == "response"
    assert execution.message_type == "response"
    assert [item.ticker for item in result.fills] == ["AAPL"]
    assert fill is not None
    order = _only(graph.descendants(fill, max_depth=1, edge_types={"EXECUTES"}))
    recommendation = _only(
        graph.descendants(order, max_depth=1, edge_types={"APPROVES"})
    )
    candidate = _only(
        graph.descendants(recommendation, max_depth=1, edge_types={"DERIVED_FROM"})
    )
    scan_node = _only(
        graph.descendants(candidate, max_depth=1, edge_types={"SURVIVED"})
    )
    snapshot = _only(
        graph.descendants(scan_node, max_depth=1, edge_types={"DERIVED_FROM"})
    )
    lineage = (order, recommendation, candidate, scan_node, snapshot)
    assert [node.label for node in lineage] == [
        "OrderIntent",
        "Recommendation",
        "Candidate",
        "ScanRun",
        "MarketSnapshot",
    ]


def _bind_pipeline(bus: InProcessBus, graph: InMemoryGraphStore) -> None:
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
    ExecutionAgent(bus, graph=graph).bind()


def _pipeline_bars() -> tuple[OHLCVBar, ...]:
    # Two bars per ticker: below every indicator window (RSI-2 needs three closes), so
    # the analyst degrades to neutral -> confidence 0.60, clearing the regime floor;
    # AAPL's wider rise keeps it the top scanner candidate by relative strength.
    return (
        bar("AAPL", 4, 100.0),
        bar("AAPL", 0, 116.0),
        bar("MSFT", 4, 100.0),
        bar("MSFT", 0, 110.0),
    )


def _scan_message() -> AgentMessage:
    return AgentMessage(
        sender="tester",
        recipient="scanner",
        message_type="request",
        capability="run_scan",
        payload={"run_id": "p3-execution-test", "universe": "fixture"},
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


def _submit_message(payload: OrderIntentSet) -> AgentMessage:
    return AgentMessage(
        sender="tester",
        recipient="execution",
        message_type="request",
        capability="submit",
        payload=payload.model_dump(mode="json"),
    )


def _only(nodes: Iterable[Node]) -> Node:
    rows = tuple(nodes)
    assert len(rows) == 1
    return rows[0]
