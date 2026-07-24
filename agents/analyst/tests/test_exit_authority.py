"""Analyst exit-authority graph-pull tests.

Agent: analyst
Role: prove breached stops force sells on the analyst rail.
External I/O: none.
"""

from __future__ import annotations

from datetime import UTC, datetime

from agents.analyst.poll import analyze_scan_node
from agents.analyst.settings import AnalystSettings
from agents.analyst.tests.helpers import bar, candidate_set
from contracts.analyst import RecommendationSet
from contracts.common import Provenance
from contracts.provider import (
    MARKET_DATA_LABEL,
    REGIME_CONTEXT_LABEL,
    DataQualityTrace,
    MarketData,
    OHLCVBar,
    RegimeContext,
)
from kernel import CollectingFaultSink, InMemoryGraphStore, Node

_RUN_ID = "risk-run"


def test_graph_pull_forces_weighted_multilot_stop_sell() -> None:
    """ADR-0017: graph-pull held stop forces sell despite high confidence."""
    graph = InMemoryGraphStore()
    sink = CollectingFaultSink()
    scan = _seed_scan(graph, _held_bars("RISK", latest_close=166.25))
    _position(graph, "a:RISK", "RISK", 1, opened_price_cents=10000, stop_pct=0.05)
    _position(graph, "b:RISK", "RISK", 3, opened_price_cents=20000, stop_pct=0.05)

    analyze_scan_node(
        scan,
        graph=graph,
        settings=AnalystSettings(exit_confidence_floor=0.01),
        sink=sink,
    )

    rec_set = _latest_recommendation_set(graph)
    rec = rec_set.recommendations[0]
    assert rec.confidence > 0.01
    assert (rec.ticker, rec.action, rec.exit_trigger) == ("RISK", "sell", "stop")
    assert "forced stop exit" in rec.rationale.summary
    assert graph.list_nodes("Recommendation")[0].props["exit_trigger"] == "stop"
    assert sink.faults == []


def test_graph_pull_sells_above_stop_when_confidence_below_floor() -> None:
    """ADR-0017: above-stop held names still use the thesis exit floor."""
    graph = InMemoryGraphStore()
    sink = CollectingFaultSink()
    scan = _seed_scan(graph, _held_bars("RISK", latest_close=110.00))
    _position(graph, "a:RISK", "RISK", 1, opened_price_cents=10000, stop_pct=0.05)

    analyze_scan_node(
        scan,
        graph=graph,
        settings=AnalystSettings(exit_confidence_floor=0.99),
        sink=sink,
    )

    rec = _latest_recommendation_set(graph).recommendations[0]
    assert (rec.ticker, rec.action, rec.exit_trigger) == ("RISK", "sell", "thesis")
    assert "thesis exit" in rec.rationale.summary
    assert sink.faults == []


def test_graph_pull_holds_above_stop_when_confidence_above_floor() -> None:
    """ADR-0017: above-stop held names stay held when alpha remains confident."""
    graph = InMemoryGraphStore()
    sink = CollectingFaultSink()
    scan = _seed_scan(graph, _held_bars("RISK", latest_close=110.00))
    _position(graph, "a:RISK", "RISK", 1, opened_price_cents=10000, stop_pct=0.05)

    analyze_scan_node(
        scan,
        graph=graph,
        settings=AnalystSettings(exit_confidence_floor=0.01),
        sink=sink,
    )

    rec = _latest_recommendation_set(graph).recommendations[0]
    assert (rec.ticker, rec.action, rec.exit_trigger) == ("RISK", "hold", None)
    assert sink.faults == []


def test_graph_pull_faults_on_multilot_different_stop_pct() -> None:
    """ADR-0017: one ticker with two stop percentages is not representable."""
    graph = InMemoryGraphStore()
    sink = CollectingFaultSink()
    scan = _seed_scan(graph, _held_bars("RISK", latest_close=100.00))
    _position(graph, "a:RISK", "RISK", 1, opened_price_cents=10000, stop_pct=0.05)
    _position(graph, "b:RISK", "RISK", 1, opened_price_cents=10000, stop_pct=0.08)

    analyze_scan_node(scan, graph=graph, sink=sink)

    rec_set = _latest_recommendation_set(graph)
    assert rec_set.recommendations == ()
    assert rec_set.rejections[0].reason == "held position stop threshold unavailable"
    assert "different stop_pct" in sink.faults[0].message
    assert graph.list_nodes("Recommendation") == ()


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
    stop_pct: float,
) -> None:
    graph.merge_node(
        "Position",
        key,
        {
            "run_id": "seed",
            "ticker": ticker,
            "quantity": quantity,
            "opened_price_cents": opened_price_cents,
            "stop_pct": stop_pct,
            "target_pct": 0.10,
            "horizon_days": 10,
            "opened_at": "2026-07-20",
            "status": "open",
        },
    )


def _latest_recommendation_set(graph: InMemoryGraphStore) -> RecommendationSet:
    node = graph.list_nodes("AnalystRun")[-1]
    return RecommendationSet.model_validate(node.props["recommendation_set"])
