"""Regime VIX graph-pull no-halt tests.

Agent: orchestration
Role: prove missing regime VIX does not halt downstream recommendations or orders.
External I/O: none.
"""

from __future__ import annotations

from agents.analyst.settings import AnalystSettings
from agents.analyst.tests.helpers import overbought_bars
from kernel import InMemoryGraphStore
from orchestration.local_pipeline import cascade_once
from orchestration.start import place_run_request
from orchestration.tests.helpers import ReboundingDataSource, entry_bars, rebound_bars
from orchestration.tests.seeded_broker import SeededPaperBroker
from orchestration.tests.test_unified_decision_run import (
    _latest_order_set,
    _position,
    _provider,
)


def test_graph_pull_missing_vix_does_not_halt_buys_or_exits() -> None:
    """PROV-OUT-02 / PROV-OUT-03 / PROV-NEV-01 / ANLZ-OUT-04 / PM-OUT-04:
    missing ^VIX warning evidence must not behave like provider degradation."""
    graph = InMemoryGraphStore()
    broker = SeededPaperBroker({"LOW": 7})
    _position(graph, "LOW", 7)
    source = ReboundingDataSource(
        entry=(*entry_bars(), *overbought_bars("LOW")),
        rebound=rebound_bars(),
        vix=None,
    )
    agent = _provider(graph, source)

    place_run_request(
        graph, run_id="missing-vix-still-trades", tickers=("AAPL", "MSFT")
    )
    cascade_once(
        graph,
        provider_agent=agent,
        broker=broker,
        analyst_settings=AnalystSettings(exit_confidence_floor=0.58),
    )

    fills = {(fill.ticker, fill.side, fill.quantity) for fill in broker.fills()}
    assert ("LOW", "sell", 7) in fills
    assert any(ticker == "AAPL" and side == "buy" for ticker, side, _qty in fills)
    regime = graph.get_node("RegimeContext", "regime-context:missing-vix-still-trades")
    assert regime is not None
    snapshot = regime.props["snapshot"]
    assert snapshot["vix_status"] == "missing"
    assert snapshot["provenance"]["incident_refs"] == ()
    rejected = _latest_order_set(graph).rejected
    assert not any(order.reason == "provider_degraded" for order in rejected)
