"""Analyst held-position scoring tests.

Agent: analyst
Role: prove bus and graph-pull paths score held tickers with explicit actions.
External I/O: none.
"""

from __future__ import annotations

from agents.analyst.poll import analyze_scan_node
from agents.analyst.settings import AnalystSettings
from agents.analyst.tests.helpers import (
    analyze_message,
    bars,
    candidate,
    candidate_set,
    overbought_bars,
    wire_analyst,
)
from contracts.common import Provenance
from contracts.provider import (
    MARKET_DATA_LABEL,
    REGIME_CONTEXT_LABEL,
    DataQualityTrace,
    MarketData,
    RegimeContext,
)
from kernel import CollectingFaultSink, InMemoryGraphStore


def test_bus_analyze_scores_scanner_survivor_plus_held_ticker() -> None:
    """ADR-0016: bus path asks provider for survivor+held and emits buy/sell."""
    scan = candidate_set(candidate("AAPL"))
    bus, graph, sink = wire_analyst(
        source_bars=(*bars(), *overbought_bars("LOW")),
        settings=AnalystSettings(exit_confidence_floor=0.58),
    )
    _position(graph, "LOW", 5)

    response = bus.request(analyze_message(scan))

    actions = {
        item["ticker"]: item["action"] for item in response.payload["recommendations"]
    }
    assert actions == {"AAPL": "buy", "LOW": "sell"}
    assert sink.faults == []


def test_graph_pull_held_ticker_without_market_data_records_fault() -> None:
    """ADR-0016: held names with no bars fault and are skipped, not crashed."""
    graph = InMemoryGraphStore()
    sink = CollectingFaultSink()
    scan = graph.merge_node(
        "ScanRun",
        "scan",
        {"candidate_set": candidate_set().model_dump(mode="json")},
    )
    market = graph.merge_node(
        MARKET_DATA_LABEL,
        "market-data:r1",
        {
            "snapshot": MarketData(
                bars=(),
                quality=DataQualityTrace(requested=1, returned=0),
                provenance=Provenance(run_id="md", source_agent="provider"),
            ).model_dump(mode="json"),
            "run_id": "r1",
        },
    )
    graph.add_edge(scan, market, "DERIVED_FROM")
    graph.merge_node(
        REGIME_CONTEXT_LABEL,
        "regime-context:r1",
        {"snapshot": _regime().model_dump(mode="json"), "run_id": "r1"},
    )
    _position(graph, "NODATA", 4)

    analyze_scan_node(scan, graph=graph, sink=sink)

    rec_set = graph.list_nodes("AnalystRun")[-1].props["recommendation_set"]
    assert rec_set["recommendations"] == ()
    assert sink.faults[0].message == "held ticker NODATA has no market data"


def _regime() -> RegimeContext:
    from datetime import UTC, datetime

    return RegimeContext(
        label="neutral",
        as_of=datetime.now(tz=UTC),
        base_min_confidence=0.55,
        base_stop_loss_pct=0.05,
        base_take_profit_pct=0.10,
        base_max_holding_days=10,
        provenance=Provenance(run_id="regime", source_agent="provider"),
    )


def _position(graph: InMemoryGraphStore, ticker: str, quantity: int) -> None:
    graph.merge_node(
        "Position",
        f"held:{ticker}",
        {"ticker": ticker, "quantity": quantity, "status": "open"},
    )
