"""MonitorAgent exit-rule + realized-PnL tests.

Agent: monitor
Role: verify stop/target/time closes and holds, with their realized PnL on close.
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


def test_stop_rule_writes_check_close_and_dispatches_execution() -> None:
    bus, graph, broker, _sink = wire_monitor(bars=(bar("AAPL", 0, 94.0),))
    seed_fill(graph)

    result = CloseDecisionSet.model_validate(bus.request(check_message()).payload)

    position = graph.get_node("Position", "pm-run-fixture:AAPL")
    assert position is not None
    assert [(item.decision, item.trigger) for item in result.decisions] == [
        ("close", "stop")
    ]
    # entry 10000c, stop exit 9400c, quantity 1 -> realized -600c.
    assert result.decisions[0].pnl_cents == -600
    close_node = next(
        node
        for node in graph.ancestors(position, max_depth=1)
        if node.label == "CloseDecision"
    )
    assert close_node.props["pnl_cents"] == -600
    assert [node.label for node in graph.ancestors(position, max_depth=1)] == [
        "Fill",
        "PositionCheck",
        "CloseDecision",
    ]
    assert broker.order_count == 1


def test_target_rule_triggers_close() -> None:
    bus, _graph, broker, _sink = wire_monitor(bars=(bar("AAPL", 0, 111.0),))
    seed_fill(_graph)

    result = CloseDecisionSet.model_validate(bus.request(check_message()).payload)

    assert [(item.decision, item.trigger) for item in result.decisions] == [
        ("close", "target")
    ]
    # entry 10000c, target exit 11100c, quantity 1 -> realized +1100c.
    assert result.decisions[0].pnl_cents == 1100
    assert broker.order_count == 1


def test_time_rule_triggers_close() -> None:
    bus, graph, _broker, _sink = wire_monitor(
        bars=(bar("AAPL", 0, 100.0),),
        settings=MonitorSettings(default_horizon_days=0),
    )
    seed_fill(graph)

    result = CloseDecisionSet.model_validate(bus.request(check_message()).payload)

    assert [(item.decision, item.trigger) for item in result.decisions] == [
        ("close", "time")
    ]
    # entry 10000c, time exit at the current 10000c price -> realized 0c (break-even).
    assert result.decisions[0].pnl_cents == 0


def test_hold_writes_check_without_close_decision() -> None:
    bus, graph, _broker, _sink = wire_monitor(
        bars=(bar("AAPL", 0, 100.0), bar("AAPL", 1, 99.0))
    )
    seed_fill(graph)

    result = CloseDecisionSet.model_validate(bus.request(check_message()).payload)

    assert [(item.decision, item.trigger) for item in result.decisions] == [
        ("hold", "none")
    ]
    assert result.decisions[0].pnl_cents is None  # holds carry no realized PnL
    assert node_count(graph, "PositionCheck") == 1
    assert node_count(graph, "CloseDecision") == 0
