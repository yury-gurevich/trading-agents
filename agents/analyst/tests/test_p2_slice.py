"""Full P2 slice integration test.

Agent: analyst
Role: verify provider to scanner to analyst provenance chain.
External I/O: none.
"""

from __future__ import annotations

from agents.analyst import AnalystAgent
from agents.analyst.tests.helpers import analyze_message, bars
from agents.provider import ProviderAgent
from agents.provider.settings import ProviderSettings
from agents.provider.sources import FakeDataSource
from agents.scanner import ScannerAgent
from agents.scanner.settings import ScannerSettings
from agents.scanner.universe import FakeUniverse
from contracts.scanner import CandidateSet
from kernel import AgentMessage, InMemoryGraphStore, InProcessBus


def test_full_p2_slice_produces_recommendation_with_complete_lineage() -> None:
    bus = InProcessBus()
    graph = InMemoryGraphStore()
    ProviderAgent(
        bus,
        graph=graph,
        source=FakeDataSource(bars=bars(), vix=12.0),
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

    scan = bus.request(
        AgentMessage(
            sender="tester",
            recipient="scanner",
            message_type="request",
            capability="run_scan",
            payload={"run_id": "p2-test", "universe": "fixture"},
        )
    )
    analysis = bus.request(analyze_message(CandidateSet.model_validate(scan.payload)))

    assert scan.message_type == "response"
    assert analysis.message_type == "response"
    assert [item["ticker"] for item in analysis.payload["recommendations"]] == ["AAPL"]
    recommendation = graph.get_node(
        "Recommendation", f"{analysis.payload['run_id']}:AAPL"
    )
    assert recommendation is not None
    candidates = list(
        graph.descendants(recommendation, max_depth=1, edge_types={"DERIVED_FROM"})
    )
    assert [node.label for node in candidates] == ["Candidate"]
    scans = list(graph.descendants(candidates[0], max_depth=1, edge_types={"SURVIVED"}))
    assert [node.label for node in scans] == ["ScanRun"]
    snapshots = list(
        graph.descendants(scans[0], max_depth=1, edge_types={"DERIVED_FROM"})
    )
    assert [node.label for node in snapshots] == ["MarketSnapshot"]
