"""Live-position safety tests for S150 stop-target proposals.

Agent: analyst
Role: prove proposal-mode flips do not mutate existing position or stop facts.
External I/O: none.
"""

from __future__ import annotations

from datetime import UTC, datetime

from agents.analyst.run import run_analysis
from agents.analyst.settings import AnalystSettings
from agents.analyst.tests.helpers import bars, candidate, candidate_set
from contracts.common import Provenance
from contracts.positions import open_positions
from contracts.provider import DataQualityTrace, MarketData, RegimeContext
from kernel import CollectingFaultSink, InMemoryGraphStore


def test_scaled_mode_does_not_reprice_existing_position_or_resting_stop() -> None:
    """MON-IDN-02 / MON-STA-02 / ADR-0015: live stop facts are untouched."""
    graph = InMemoryGraphStore()
    position = graph.merge_node(
        "Position",
        "pos:AAPL",
        {
            "ticker": "AAPL",
            "quantity": 5,
            "opened_price_cents": 10000,
            "stop_pct": 0.05,
        },
    )
    ref = open_positions(graph)[0].position_ref
    stop = graph.merge_node(
        "BrokerStopOrder",
        f"stop:{ref}:AAPL",
        {
            "ticker": "AAPL",
            "position_ref": ref,
            "stop_price_cents": 9500,
            "broker_order_id": "broker-stop-aapl",
            "placed_at": "2026-07-30T00:00:00+00:00",
        },
    )
    before_position = dict(position.props)
    before_stop = dict(stop.props)

    result = run_analysis(
        graph,
        candidate_set(candidate("AAPL")),
        _market(),
        _regime(),
        AnalystSettings(stop_target_mode="scaled"),
        CollectingFaultSink(),
        held_positions=open_positions(graph),
    )

    after_position = graph.get_node("Position", "pos:AAPL")
    after_stop = graph.get_node("BrokerStopOrder", f"stop:{ref}:AAPL")
    assert result.recommendations
    assert after_position is not None
    assert after_stop is not None
    assert after_position.props == before_position
    assert after_stop.props == before_stop


def _market() -> MarketData:
    return MarketData(
        bars=bars(),
        benchmark=bars(),
        quality=DataQualityTrace(requested=1, returned=1),
        provenance=Provenance(run_id="market-fixture", source_agent="provider"),
    )


def _regime() -> RegimeContext:
    return RegimeContext(
        label="risk_on",
        vix=12.0,
        as_of=datetime.now(tz=UTC),
        base_min_confidence=0.30,
        base_stop_loss_pct=0.05,
        base_take_profit_pct=0.10,
        base_max_holding_days=10,
        provenance=Provenance(run_id="regime-fixture", source_agent="provider"),
    )
