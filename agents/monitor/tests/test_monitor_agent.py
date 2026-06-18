"""MonitorAgent capability tests.

Agent: monitor
Role: verify position opening, exit rules, provider degradation, and hold explains.
External I/O: none.
"""

from __future__ import annotations

from agents.monitor import MonitorAgent
from agents.monitor.tests.helpers import (
    bar,
    check_message,
    explain_message,
    node_count,
    seed_fill,
    wire_monitor,
)
from contracts.common import Explanation
from contracts.monitor import CloseDecisionSet
from kernel import CollectingFaultSink, InMemoryGraphStore, InProcessBus


def test_check_positions_opens_position_idempotently() -> None:
    bus, graph, broker, _sink = wire_monitor(bars=(bar("AAPL", 0, 100.0),))
    seed_fill(graph)

    first = CloseDecisionSet.model_validate(bus.request(check_message()).payload)
    second = CloseDecisionSet.model_validate(bus.request(check_message()).payload)

    assert [item.decision for item in first.decisions] == ["hold"]
    assert [item.decision for item in second.decisions] == ["hold"]
    assert node_count(graph, "Position") == 1
    assert broker.order_count == 0


def test_provider_failure_skips_position_and_records_fault() -> None:
    bus, graph, _broker, sink = wire_monitor(fail_ohlcv=True)
    seed_fill(graph)

    result = CloseDecisionSet.model_validate(bus.request(check_message()).payload)

    assert result.decisions == ()
    assert result.positions_checked == 0
    assert node_count(graph, "Position") == 1
    assert len(sink.faults) == 1


def test_missing_provider_handler_skips_position_and_records_fault() -> None:
    bus = InProcessBus()
    graph = InMemoryGraphStore()
    sink = CollectingFaultSink()
    MonitorAgent(bus, graph=graph, sink=sink).bind()
    seed_fill(graph)

    result = CloseDecisionSet.model_validate(bus.request(check_message()).payload)

    assert result.decisions == ()
    assert len(sink.faults) == 1


def test_missing_current_price_skips_position_and_records_fault() -> None:
    bus, graph, _broker, sink = wire_monitor(bars=(bar("MSFT", 0, 100.0),))
    seed_fill(graph)

    result = CloseDecisionSet.model_validate(bus.request(check_message()).payload)

    assert result.decisions == ()
    assert len(sink.faults) == 1


def test_missing_stop_target_uses_fallback_and_records_fault() -> None:
    bus, graph, _broker, sink = wire_monitor(bars=(bar("AAPL", 0, 100.0),))
    seed_fill(graph, stop_pct=None, target_pct=None)

    result = CloseDecisionSet.model_validate(bus.request(check_message()).payload)

    position = graph.get_node("Position", "pm-run-fixture:AAPL")
    assert [(item.decision, item.trigger) for item in result.decisions] == [
        ("hold", "none")
    ]
    assert position is not None
    assert position.props["stop_pct"] == 0.05
    assert position.props["target_pct"] == 0.10
    assert len(sink.faults) == 1


def test_execution_dispatch_error_records_fault_after_close_decision() -> None:
    bus = InProcessBus()
    graph = InMemoryGraphStore()
    sink = CollectingFaultSink()
    from agents.provider import ProviderAgent
    from agents.provider.settings import ProviderSettings
    from agents.provider.sources import FakeDataSource

    ProviderAgent(
        bus,
        graph=graph,
        source=FakeDataSource(bars=(bar("AAPL", 0, 94.0),), vix=12.0),
        settings=ProviderSettings(max_staleness_days=7),
    ).bind()
    MonitorAgent(bus, graph=graph, sink=sink).bind()
    seed_fill(graph)

    result = CloseDecisionSet.model_validate(bus.request(check_message()).payload)

    assert result.decisions[0].decision == "close"
    assert len(sink.faults) == 1


def test_check_positions_without_fills_returns_empty_result() -> None:
    bus, _graph, _broker, sink = wire_monitor()

    result = CloseDecisionSet.model_validate(bus.request(check_message()).payload)

    assert result.decisions == ()
    assert sink.faults == []


def test_explain_hold_returns_non_empty_explanation() -> None:
    bus, graph, _broker, _sink = wire_monitor(bars=(bar("AAPL", 0, 100.0),))
    seed_fill(graph)
    bus.request(check_message())

    explanation = Explanation.model_validate(bus.request(explain_message()).payload)

    assert "Held 1 open positions" in explanation.summary
    assert explanation.evidence_refs == ("monitor.exit_rules",)


def test_explain_hold_without_position_returns_explanation() -> None:
    bus, _graph, _broker, _sink = wire_monitor()

    explanation = Explanation.model_validate(bus.request(explain_message()).payload)

    assert "No open held positions" in explanation.summary
    assert explanation.evidence_refs == ("monitor.positions",)
