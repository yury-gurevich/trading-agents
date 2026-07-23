"""MonitorAgent exit-rule + realized-PnL tests.

Agent: monitor
Role: verify stop/target/time closes and holds, with their realized PnL on close.
External I/O: none.
"""

from __future__ import annotations

from decimal import Decimal

from agents.monitor.settings import MonitorSettings
from agents.monitor.tests.helpers import (
    bar,
    check_message,
    node_count,
    seed_fill,
    wire_monitor,
)
from contracts.common import Money
from contracts.monitor import CloseDecisionSet


def test_stop_rule_writes_check_close_and_dispatches_execution() -> None:
    """MON-OUT-02 / MON-OUT-03 / MON-NEV-01: stop rule → CloseDecision +
    PositionCheck nodes; pnl_cents set."""
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
    """MON-OUT-02 / MON-OUT-03: target rule → close decision with pnl_cents."""
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
    """MON-OUT-02 / MON-OUT-03: horizon=0 → time trigger; pnl_cents 0."""
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
    """MON-OUT-02 / MON-OUT-05: hold → PositionCheck written;
    no CloseDecision; pnl_cents None."""
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


def test_close_sells_whole_position_at_decided_price() -> None:
    """MON-OUT-02 / EXEC-IN-02: the exit order carries the position's real size and
    the price the exit was decided at, not an execution-side fixture default."""
    bus, graph, broker, _sink = wire_monitor(bars=(bar("AAPL", 0, 94.0),))
    seed_fill(graph, quantity=55)

    result = CloseDecisionSet.model_validate(bus.request(check_message()).payload)

    decision = result.decisions[0]
    assert (decision.decision, decision.trigger) == ("close", "stop")
    assert decision.quantity == 55
    assert decision.reference_price_cents == 9400
    # The broker must see the whole position sold at the decided price. Before this
    # was wired, execution sold 1 share at a $1.00 limit and the stop never landed.
    sell = next(fill for fill in broker.fills() if fill.side == "sell")
    assert sell.quantity == 55
    assert sell.price == Money(amount=Decimal("94.00"))
