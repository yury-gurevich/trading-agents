"""Analyst broker-stop deferral tests.

Agent: analyst
Role: prove broker-native stops gate the analyst forced-stop fallback.
External I/O: none.
"""

from __future__ import annotations

from datetime import UTC, datetime

from agents.analyst.poll import analyze_scan_node
from agents.analyst.settings import AnalystSettings
from agents.analyst.tests.helpers import bar, candidate_set
from contracts.analyst import RecommendationSet
from contracts.common import Provenance
from contracts.positions import open_positions
from contracts.provider import (
    MARKET_DATA_LABEL,
    REGIME_CONTEXT_LABEL,
    DataQualityTrace,
    MarketData,
    OHLCVBar,
    RegimeContext,
)
from kernel import CollectingFaultSink, InMemoryGraphStore, Node

_RUN_ID = "broker-stop-run"


def test_graph_pull_defers_forced_stop_when_live_broker_stop_exists() -> None:
    graph = InMemoryGraphStore()
    sink = CollectingFaultSink()
    scan = _seed_scan(graph, _held_bars("RISK", latest_close=94.00))
    _position(graph, "held:RISK", "RISK", 1, opened_price_cents=10000)
    ref = _position_ref(graph)
    graph.merge_node(
        "BrokerStopOrder",
        f"stop:{ref}:RISK",
        {
            "ticker": "RISK",
            "position_ref": ref,
            "stop_price_cents": 9500,
            "broker_order_id": "broker-stop-1",
            "placed_at": "2026-07-25T00:00:00+00:00",
        },
    )

    analyze_scan_node(
        scan,
        graph=graph,
        settings=AnalystSettings(exit_confidence_floor=0.01),
        sink=sink,
    )

    rec = _latest_recommendation_set(graph).recommendations[0]
    assert (rec.ticker, rec.action, rec.exit_trigger) == ("RISK", "hold", None)
    assert "forced stop exit" not in rec.rationale.summary
    assert sink.faults == []


def _seed_scan(graph: InMemoryGraphStore, market_bars: tuple[OHLCVBar, ...]) -> Node:
    scan = graph.merge_node(
        "ScanRun",
        "scan-risk",
        {"candidate_set": candidate_set().model_dump(mode="json")},
    )
    market = graph.merge_node(
        MARKET_DATA_LABEL,
        f"market-data:{_RUN_ID}",
        {
            "snapshot": MarketData(
                bars=market_bars,
                quality=DataQualityTrace(
                    requested=len(market_bars), returned=len(market_bars)
                ),
                provenance=Provenance(run_id=_RUN_ID, source_agent="provider"),
            ).model_dump(mode="json"),
            "run_id": _RUN_ID,
        },
    )
    graph.add_edge(scan, market, "DERIVED_FROM")
    graph.merge_node(
        REGIME_CONTEXT_LABEL,
        f"regime-context:{_RUN_ID}",
        {"snapshot": _regime().model_dump(mode="json"), "run_id": _RUN_ID},
    )
    return scan


def _held_bars(ticker: str, *, latest_close: float) -> tuple[OHLCVBar, ...]:
    return (bar(ticker, 4, 100.00), bar(ticker, 0, latest_close))


def _regime() -> RegimeContext:
    return RegimeContext(
        label="neutral",
        as_of=datetime.now(tz=UTC),
        base_min_confidence=0.55,
        base_stop_loss_pct=0.05,
        base_take_profit_pct=0.10,
        base_max_holding_days=10,
        provenance=Provenance(run_id="regime", source_agent="provider"),
    )


def _position(
    graph: InMemoryGraphStore,
    key: str,
    ticker: str,
    quantity: int,
    *,
    opened_price_cents: int,
) -> None:
    graph.merge_node(
        "Position",
        key,
        {
            "run_id": "seed",
            "ticker": ticker,
            "quantity": quantity,
            "opened_price_cents": opened_price_cents,
            "stop_pct": 0.05,
            "target_pct": 0.10,
            "horizon_days": 10,
            "opened_at": "2026-07-20",
            "status": "open",
        },
    )


def _position_ref(graph: InMemoryGraphStore) -> str:
    return open_positions(graph)[0].position_ref


def _latest_recommendation_set(graph: InMemoryGraphStore) -> RecommendationSet:
    node = graph.list_nodes("AnalystRun")[-1]
    return RecommendationSet.model_validate(node.props["recommendation_set"])
