"""MonitorAgent capability tests.

Agent: monitor
Role: verify position opening, stop observation, provider degradation, and explains.
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
from kernel import (
    CollectingFaultSink,
    GraphFaultSink,
    InMemoryGraphStore,
    InProcessBus,
)


def test_check_positions_opens_position_idempotently() -> None:
    """MON-IN-01 / MON-TRG-01 / MON-OUT-01 / MON-IDM-02: RPC path;
    Position opened once."""
    bus, graph, broker, _sink = wire_monitor(bars=(bar("AAPL", 0, 100.0),))
    seed_fill(graph)

    first = CloseDecisionSet.model_validate(bus.request(check_message()).payload)
    second = CloseDecisionSet.model_validate(bus.request(check_message()).payload)

    assert first.decisions == ()
    assert second.decisions == ()
    assert first.positions_checked == 1
    assert second.positions_checked == 1
    assert node_count(graph, "Position") == 1
    assert broker.order_count == 0


def test_provider_failure_skips_position_and_records_fault() -> None:
    """MON-OUT-07 / MON-FAIL-01 / MON-NEV-03: provider degraded → empty + fault."""
    bus, graph, _broker, sink = wire_monitor(fail_ohlcv=True)
    seed_fill(graph)

    result = CloseDecisionSet.model_validate(bus.request(check_message()).payload)

    assert result.decisions == ()
    assert result.positions_checked == 0
    assert node_count(graph, "Position") == 1
    assert len(sink.faults) == 1


def test_missing_provider_handler_skips_position_and_records_fault() -> None:
    """MON-FAIL-01 / MON-NEV-03: bus error → empty result; no direct API call."""
    bus = InProcessBus()
    graph = InMemoryGraphStore()
    sink = CollectingFaultSink()
    MonitorAgent(bus, graph=graph, sink=sink).bind()
    seed_fill(graph)

    result = CloseDecisionSet.model_validate(bus.request(check_message()).payload)

    assert result.decisions == ()
    assert len(sink.faults) == 1


def test_missing_current_price_skips_position_and_records_fault() -> None:
    """MON-NEV-04 / MON-FAIL-02: ticker missing from price → fault; position skipped."""
    bus, graph, _broker, sink = wire_monitor(bars=(bar("MSFT", 0, 100.0),))
    seed_fill(graph)

    result = CloseDecisionSet.model_validate(bus.request(check_message()).payload)

    assert result.decisions == ()
    assert len(sink.faults) == 1


def test_missing_stop_target_uses_fallback_and_records_fault() -> None:
    """MON-FAIL-03 / MON-STA-01: missing stop/target → fallback used; fault."""
    bus, graph, _broker, sink = wire_monitor(bars=(bar("AAPL", 0, 100.0),))
    seed_fill(graph, stop_pct=None, target_pct=None)

    result = CloseDecisionSet.model_validate(bus.request(check_message()).payload)

    position = graph.get_node("Position", "pm-run-fixture:AAPL")
    assert result.decisions == ()
    assert result.positions_checked == 1
    assert position is not None
    assert position.props["stop_pct"] == 0.05
    assert position.props["target_pct"] == 0.10
    assert len(sink.faults) == 1


def test_stop_breach_records_fault_without_execution_dispatch() -> None:
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

    assert result.decisions == ()
    assert graph.list_nodes("CloseDecision") == ()
    assert graph.list_nodes("Fault")[0].props["message"] == (
        "stop breached on AAPL, still held"
    )
    assert len(sink.faults) == 1


def test_check_positions_without_fills_returns_empty_result() -> None:
    """MON-IN-01 / MON-OUT-01: no fills → empty CloseDecisionSet; no faults."""
    bus, _graph, _broker, sink = wire_monitor()

    result = CloseDecisionSet.model_validate(bus.request(check_message()).payload)

    assert result.decisions == ()
    assert sink.faults == []


def test_explain_hold_returns_non_empty_explanation() -> None:
    """MON-IN-02 / MON-TRG-03: explain_hold returns Explanation; no graph write."""
    bus, graph, _broker, _sink = wire_monitor(bars=(bar("AAPL", 0, 100.0),))
    seed_fill(graph)
    bus.request(check_message())

    explanation = Explanation.model_validate(bus.request(explain_message()).payload)

    assert "Held 1 open positions" in explanation.summary
    assert explanation.evidence_refs == ("contracts.stop_rule",)


def test_explain_hold_without_position_returns_explanation() -> None:
    """MON-IN-02 / MON-TRG-03: no positions → non-empty Explanation still returned."""
    bus, _graph, _broker, _sink = wire_monitor()

    explanation = Explanation.model_validate(bus.request(explain_message()).payload)

    assert "No open held positions" in explanation.summary
    assert explanation.evidence_refs == ("monitor.positions",)


def test_stop_breach_fault_survives_the_process() -> None:
    """ADR-0017: a held breached stop is persisted as a Fault node."""
    graph = InMemoryGraphStore()
    sink = GraphFaultSink(graph, CollectingFaultSink())
    bus = InProcessBus()
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

    assert result.decisions == ()
    faults = graph.list_nodes("Fault")
    assert [node.props["source_agent"] for node in faults] == ["monitor"]
    assert faults[0].props["source_module"] == "agents.monitor.decide"
    assert faults[0].props["capability"] == "check_positions"
