"""The analyst's held-stop check reads the decided stop (S251 D6, DRIFT-074, DL-260).

Agent: analyst
Role: prove on the 2026-09-25 USB shape (adopted at the monitor's 5 % fallback, PM
      lineage 4.03 %) that the held-stop check reads the shared stop-width resolver:
      a close at or below the decided stop is a forced stop sell, a close above it
      is not, and a position whose broker stop is live is left to that stop.
External I/O: none (in-memory graph, paper broker).
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import TYPE_CHECKING

import pytest

from agents.analyst.run import run_analysis
from agents.analyst.settings import AnalystSettings
from agents.analyst.tests.helpers import candidate_set
from agents.execution.paper_broker import PaperBroker
from agents.execution.tests.stop_realign_helpers import (
    DECIDED_STOP_CENTS,
    FALLBACK_STOP_CENTS,
    OPENED_CENTS,
    seed_usb,
    seed_usb_stop,
)
from contracts.broker_stops import active_broker_stop_refs
from contracts.common import Provenance
from contracts.positions import open_position_stop_thresholds, open_positions
from contracts.provider import DataQualityTrace, MarketData, OHLCVBar, RegimeContext
from kernel import CollectingFaultSink, InMemoryGraphStore

if TYPE_CHECKING:
    from contracts.analyst import Recommendation


def _bar(day: int, close: float) -> OHLCVBar:
    return OHLCVBar(
        ticker="USB",
        bar_date=date(2026, 9, day),
        open=close,
        high=close + 0.10,
        low=close - 0.10,
        close=close,
        volume=1_000_000,
    )


def _usb_decision(graph: InMemoryGraphStore, latest_close: float) -> Recommendation:
    bars = (_bar(24, OPENED_CENTS / 100), _bar(25, latest_close))
    market = MarketData(
        bars=bars,
        quality=DataQualityTrace(requested=2, returned=2),
        provenance=Provenance(run_id="sched-2026-09-25", source_agent="provider"),
    )
    regime = RegimeContext(
        label="neutral",
        as_of=datetime(2026, 9, 25, tzinfo=UTC),
        base_min_confidence=0.55,
        base_stop_loss_pct=0.05,
        base_take_profit_pct=0.10,
        base_max_holding_days=10,
        provenance=Provenance(run_id="regime", source_agent="provider"),
    )
    sink = CollectingFaultSink()
    result = run_analysis(
        graph,
        candidate_set(),
        market,
        regime,
        AnalystSettings(exit_confidence_floor=0.0),
        sink,
        held_positions=open_positions(graph),
    )
    assert sink.faults == []
    [usb] = [rec for rec in result.recommendations if rec.ticker == "USB"]
    return usb


@pytest.mark.parametrize(
    "latest_close",
    [DECIDED_STOP_CENTS / 100, 57.60],
    ids=["at-the-decided-stop", "beyond-it-above-the-fallback"],
)
def test_a_close_at_or_beyond_the_decided_stop_is_a_forced_stop_sell(
    latest_close: float,
) -> None:
    """ANLZ-OUT-09 (DRIFT-074, ADR-0017): the check reads the shared resolver, so
    the threshold is the PM's decided 58.06, not the adopted 5 % (57.47). A close at
    it, or at 57.60 (beyond it and still above the fallback stop), is a sell with
    exit_trigger 'stop', whatever the confidence."""
    graph = InMemoryGraphStore()
    seed_usb(graph)
    [threshold] = open_position_stop_thresholds(graph)
    assert FALLBACK_STOP_CENTS < latest_close * 100 <= DECIDED_STOP_CENTS

    usb = _usb_decision(graph, latest_close)

    assert threshold.opened_price_cents == OPENED_CENTS
    assert (usb.action, usb.exit_trigger) == ("sell", "stop")
    assert "forced stop exit" in usb.rationale.summary


def test_a_close_above_the_decided_stop_is_no_stop_exit() -> None:
    """ANLZ-OUT-09: one cent above the decided stop is not a breach; the held name
    is judged on its thesis (here it holds)."""
    graph = InMemoryGraphStore()
    seed_usb(graph)

    usb = _usb_decision(graph, (DECIDED_STOP_CENTS + 1) / 100)

    assert (usb.action, usb.exit_trigger) == ("hold", None)


def test_a_position_with_a_live_broker_stop_is_left_to_that_stop() -> None:
    """ANLZ-OUT-09: when the position's broker stop is live, the broker stop owns
    the exit; the analyst's check reports no breach even beyond the decided stop."""
    graph = InMemoryGraphStore()
    seed_usb(graph)
    seed_usb_stop(graph, PaperBroker())
    [position] = open_positions(graph)
    assert position.position_ref in active_broker_stop_refs(graph)

    usb = _usb_decision(graph, 57.60)

    assert usb.exit_trigger != "stop"
