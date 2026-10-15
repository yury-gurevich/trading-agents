"""A6-A10: stop-width readers share one lazy Fill read per pass (S279).

Agent: tests
Role: prove per-ticker width equivalence, empty-read bounds and lone-call compatibility.
External I/O: none.
"""

from __future__ import annotations

from tests.label_reads_support import PRICES, WIDTHS, LabelReadCounter, seed_book

from agents.execution.broker_stop_thresholds import broker_stop_thresholds
from agents.monitor.position_book import active_positions
from agents.monitor.run import evaluate_and_write
from contracts.positions import open_position_stop_thresholds
from contracts.stop_width import decided_stop_pct
from kernel import CollectingFaultSink


def test_a6_the_analysts_held_book_reads_fill_once() -> None:
    """ANLZ-PERF-02 / ANLZ-OUT-09: each held ticker keeps its decided width."""
    graph = LabelReadCounter()
    seed_book(graph)

    thresholds = open_position_stop_thresholds(graph)

    assert {item.ticker: item.stop_pct for item in thresholds} == WIDTHS
    assert graph.listed["Fill"] == 1


def test_a7_executions_stop_plan_reads_fill_once() -> None:
    """EXEC-PERF-02 / EXEC-OBS-06: the plan retains every width and lineage source."""
    graph = LabelReadCounter()
    seed_book(graph)

    result = broker_stop_thresholds(graph, fallback_stop_pct=0.05)

    assert not result.errors
    assert {
        plan.threshold.ticker: plan.threshold.stop_pct for plan in result.plans
    } == (WIDTHS)
    assert [plan.stop_pct_source for plan in result.plans] == ["lineage"] * 3
    assert graph.listed["Fill"] == 1


def test_a8_the_monitors_evaluation_reads_fill_once() -> None:
    """MON-PERF-03 / MON-TRG-02: only AAA breaches its decided (not fallback) stop."""
    graph = LabelReadCounter()
    seed_book(graph)
    positions = active_positions(graph)
    sink = CollectingFaultSink()
    before = graph.listed["Fill"]

    result = evaluate_and_write(
        graph,
        sink,
        source_run_id="pm-run-evaluation",
        positions=positions,
        prices=PRICES,
    )

    assert graph.listed["Fill"] - before == 1
    assert result.positions_checked == 3
    run = graph.get_node("MonitorRun", result.run_id)
    assert run is not None
    assert (run.props["positions_checked"], run.props["stop_breaches"]) == (3, 1)
    assert {
        check.props["ticker"]: check.props["stop_breached"]
        for check in graph.list_nodes("PositionCheck")
    } == {"AAA": True, "BBB": False, "CCC": False}
    assert [fault.error_type for fault in sink.faults] == ["StopBreached"]


def test_a9_a_book_with_no_adopted_position_reads_no_fill() -> None:
    """EXEC-PERF-02 / MON-PERF-03 / ANLZ-PERF-02: each pass stays lazy."""
    graph = LabelReadCounter()
    seed_book(graph, adopted=False)

    thresholds = open_position_stop_thresholds(graph)
    plans = broker_stop_thresholds(graph, fallback_stop_pct=0.05)
    result = evaluate_and_write(
        graph,
        CollectingFaultSink(),
        source_run_id="pm-run-not-adopted",
        positions=active_positions(graph),
        prices=PRICES,
    )

    assert {item.ticker: item.stop_pct for item in thresholds} == WIDTHS
    assert not plans.errors
    assert {plan.threshold.ticker: plan.threshold.stop_pct for plan in plans.plans} == (
        WIDTHS
    )
    assert [plan.stop_pct_source for plan in plans.plans] == ["position"] * 3
    assert result.positions_checked == 3
    assert graph.listed["Fill"] == 0


def test_a10_a_lone_call_still_reads_its_lineage() -> None:
    """EXEC-OBS-06 / ANLZ-OUT-09: optional sharing preserves lone-call lineage."""
    from contracts.stop_width import LineageFills

    graph = LabelReadCounter()
    positions = seed_book(graph)

    assert decided_stop_pct(graph, positions[0]) == (0.02, "lineage")
    assert graph.listed["Fill"] == 1
    fills = LineageFills(graph)
    assert graph.listed["Fill"] == 1
    assert decided_stop_pct(graph, positions[1], fills=fills) == (0.07, "lineage")
    assert decided_stop_pct(graph, positions[2], fills=fills) == (0.035, "lineage")
    assert graph.listed["Fill"] == 2
