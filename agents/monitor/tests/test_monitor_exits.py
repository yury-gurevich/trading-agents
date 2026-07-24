"""Monitor stop-observation tests.

Agent: monitor
Role: verify stop breaches become Faults, not CloseDecisions or broker dispatches.
External I/O: none.
"""

from __future__ import annotations

from agents.monitor.settings import MonitorSettings
from agents.monitor.tests.helpers import (
    bar,
    check_message,
    node_count,
    seed_fill,
    wire_monitor,
)
from contracts.monitor import CloseDecisionSet


def test_stop_breach_writes_check_fault_and_no_close_or_dispatch() -> None:
    """ADR-0017: breached stop is surfaced, never dispatched by monitor."""
    bus, graph, broker, sink = wire_monitor(bars=(bar("AAPL", 0, 94.0),))
    seed_fill(graph)

    result = CloseDecisionSet.model_validate(bus.request(check_message()).payload)

    check = graph.list_nodes("PositionCheck")[0]
    assert result.decisions == ()
    assert result.positions_checked == 1
    assert check.props["observation"] == "stop_breached"
    assert check.props["stop_breached"] is True
    assert check.props["trigger"] == "stop"
    assert node_count(graph, "CloseDecision") == 0
    assert broker.order_count == 0
    assert [fault.message for fault in sink.faults] == [
        "stop breached on AAPL, still held"
    ]
    assert graph.list_nodes("Fault")[0].props["error_type"] == "StopBreached"


def test_target_rule_is_retired_without_exit_or_fault() -> None:
    """ADR-0017: target exits are deferred strategy, not monitor mechanics."""
    bus, graph, broker, sink = wire_monitor(bars=(bar("AAPL", 0, 111.0),))
    seed_fill(graph)

    result = CloseDecisionSet.model_validate(bus.request(check_message()).payload)

    assert result.decisions == ()
    assert result.positions_checked == 1
    assert graph.list_nodes("PositionCheck")[0].props["observation"] == "clear"
    assert node_count(graph, "CloseDecision") == 0
    assert broker.order_count == 0
    assert sink.faults == []


def test_time_rule_is_retired_without_exit_or_fault() -> None:
    """ADR-0017: horizon exits are deferred strategy, not monitor mechanics."""
    bus, graph, broker, sink = wire_monitor(
        bars=(bar("AAPL", 0, 100.0),),
        settings=MonitorSettings(default_horizon_days=0),
    )
    seed_fill(graph)

    result = CloseDecisionSet.model_validate(bus.request(check_message()).payload)

    assert result.decisions == ()
    assert result.positions_checked == 1
    assert node_count(graph, "CloseDecision") == 0
    assert broker.order_count == 0
    assert sink.faults == []


def test_clear_position_writes_check_without_close_decision() -> None:
    """ADR-0017: clear stop observation writes only PositionCheck evidence."""
    bus, graph, broker, sink = wire_monitor(
        bars=(bar("AAPL", 0, 100.0), bar("AAPL", 1, 99.0))
    )
    seed_fill(graph)

    result = CloseDecisionSet.model_validate(bus.request(check_message()).payload)

    assert result.decisions == ()
    assert result.positions_checked == 1
    assert graph.list_nodes("PositionCheck")[0].props["stop_breached"] is False
    assert node_count(graph, "CloseDecision") == 0
    assert broker.order_count == 0
    assert sink.faults == []
