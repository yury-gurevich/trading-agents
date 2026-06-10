"""Full P3 reporter lineage integration test.

Agent: reporter
Role: verify provider through reporter produces a closed-trade report and story.
External I/O: none.
"""

from __future__ import annotations

from agents.execution.broker import PaperBroker
from agents.reporter.tests.helpers import bar, narrative_message, report_message
from agents.reporter.tests.p3_helpers import (
    analysis_message,
    assert_complete_chain,
    assert_reporter_outputs,
    bind_pipeline,
    bind_provider,
    entry_bars,
    monitor_message,
    orders_message,
    scan_message,
    submit_message,
)
from contracts.analyst import RecommendationSet
from contracts.monitor import CloseDecisionSet
from contracts.portfolio_manager import OrderIntentSet
from contracts.reporter import RunSnapshot, TradeNarrative
from contracts.scanner import CandidateSet
from kernel import InMemoryGraphStore, InProcessBus


def test_full_p3_exit_produces_report_and_trade_narrative() -> None:
    bus = InProcessBus()
    graph = InMemoryGraphStore()
    broker = PaperBroker()
    bind_pipeline(bus, graph, broker, entry_bars())

    scan = bus.request(scan_message())
    analysis = bus.request(analysis_message(CandidateSet.model_validate(scan.payload)))
    orders = bus.request(
        orders_message(RecommendationSet.model_validate(analysis.payload))
    )
    execution = bus.request(
        submit_message(OrderIntentSet.model_validate(orders.payload))
    )
    bind_provider(bus, graph, (bar("AAPL", 0, 100.0),))
    monitor = bus.request(monitor_message(str(orders.payload["run_id"])))
    report = bus.request(report_message(str(orders.payload["run_id"])))
    narrative = bus.request(narrative_message(f"{orders.payload['run_id']}:AAPL"))

    snapshot = RunSnapshot.model_validate(report.payload)
    story = TradeNarrative.model_validate(narrative.payload)
    close_set = CloseDecisionSet.model_validate(monitor.payload)
    assert [item.message_type for item in (scan, analysis, orders, execution)] == [
        "response",
        "response",
        "response",
        "response",
    ]
    assert [item.message_type for item in (monitor, report, narrative)] == [
        "response",
        "response",
        "response",
    ]
    assert snapshot.portfolio_metrics["positions_opened"] >= 1
    assert snapshot.portfolio_metrics["positions_closed"] >= 1
    assert snapshot.signal_metrics["recommendation_count"] >= 1
    assert snapshot.headline.summary
    assert "AAPL" in story.story.summary
    assert [(item.decision, item.trigger) for item in close_set.decisions] == [
        ("close", "stop")
    ]
    assert_reporter_outputs(graph, str(orders.payload["run_id"]))
    assert_complete_chain(graph)
