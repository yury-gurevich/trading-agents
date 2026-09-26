"""S234 fact selection: what a brief says, read from the graph as its owners wrote it.

Agent: orchestration
Role: prove fills, orders, the reference run and needs-you come from stored facts.
External I/O: none.
"""

from __future__ import annotations

import pytest

from kernel import InMemoryGraphStore
from orchestration.tests.daily_brief_fixtures import (
    DAY,
    PREVIOUS_DAY,
    metrics_with,
    performance,
    pm_key,
    seed_run,
)
from orchestration.tests.daily_brief_scenarios import (
    MINUS,
    add_fill,
    brief_lines,
    seed_pair,
)

_FILLED = {"broker_status": "filled"}


def test_a8_only_fills_that_became_known_since_the_previous_brief() -> None:
    """DSP-OUT-06: a fill counts by broker_status_refreshed_at, never submitted_at.

    The window is (previous briefed PMRun, this PMRun]; a resting stop's fill reads
    `stopped out`; a fill still pending, or known outside the window, is not listed.
    """
    graph = InMemoryGraphStore()
    seed_pair(graph)  # PMRuns at 2026-09-24T22:40 and 2026-09-25T22:41
    known = "broker_status_refreshed_at"
    add_fill(graph, "before", **_FILLED, **{known: "2026-09-24T14:15:00+00:00"})
    add_fill(graph, "edge", **_FILLED, **{known: "2026-09-24T22:40:00+00:00"})
    xom = {"broker_price_cents": 11002, known: "2026-09-25T14:30:00+00:00"}
    add_fill(graph, "xom", **_FILLED, **xom)
    add_fill(
        graph,
        "ko",
        side="sell",
        quantity=20,
        stop_order_key="stop:KO",
        broker_price_cents=5810,
        **_FILLED,
        **{known: "2026-09-25T15:00:00"},  # naive: read as UTC
    )
    add_fill(graph, "mmm", **_FILLED, **{known: "2026-09-25T22:41:00+00:00"})
    add_fill(graph, "after", **_FILLED, **{known: "2026-09-25T23:10:00+00:00"})
    add_fill(graph, "vz", broker_status="accepted", **{known: "2026-09-25T14:31:00Z"})
    add_fill(graph, "pg", submitted_at="2026-09-25T14:00:00+00:00", **_FILLED)
    add_fill(graph, "bad", **_FILLED, **{known: "yesterday"})

    assert brief_lines(graph)[4] == (
        "Filled: BUY 10 XOM @ $110.02 · SELL 20 KO @ $58.10 stopped out · BUY 10 MMM"
    )


def test_orders_are_this_runs_fills_including_a_resumed_runs() -> None:
    """DSP-OUT-06: orders are the Fills whose source is this run's PM decision.

    A limit reads as the bound it accepts; a rejected order says so; another run's
    order is not listed. A resumed run's PMRun names the decision its Fills carry.
    """
    graph = InMemoryGraphStore()
    seed_pair(graph)
    source = {"source_run_id": pm_key(DAY)}
    limit = "order_applied_limit_price_cents"
    add_fill(graph, "bmy", quantity=16, status="pending", **source, **{limit: 6182})
    add_fill(graph, "xom", side="sell", **source, **{limit: 11000})
    add_fill(graph, "t", quantity=5, status="rejected", **source)
    add_fill(graph, "old", source_run_id=pm_key(PREVIOUS_DAY))
    resumed = InMemoryGraphStore()
    seed_run(resumed, pm_created="2026-09-25T22:41:00+00:00")
    resumed.merge_node("PMRun", pm_key(DAY), {"linked_from_key": "pm-original"})
    add_fill(resumed, "abt", source_run_id="pm-original")

    assert brief_lines(graph)[3] == (
        "Orders: BUY 16 BMY ≤ $61.82 · BUY 5 T rejected · SELL 10 XOM ≥ $110.00"
    )
    assert brief_lines(resumed)[3] == "Orders: BUY 10 ABT"


def test_the_reference_is_the_previous_scheduled_run_by_pm_time() -> None:
    """DSP-OUT-06: the change is against the latest earlier scheduled run's figure.

    A manual run between them, a later run, a Snapshot with no PMRun and a second
    Snapshot of this same run are none of them a reference (DL-231); the fills
    window still spans the manual run.
    """
    graph = InMemoryGraphStore()
    seed_pair(graph)
    seed_run(graph, DAY, pm_created="2026-09-25T14:15:00Z", prefix="manual")
    seed_run(graph, DAY.replace(day=28), pm_created="2026-09-28T22:41Z")
    graph.merge_node("Snapshot", "snapshot:orphan", {"run_id": "pm-missing"})
    graph.merge_node("PMRun", "pm-loose", {"created_at": "2026-09-25T20:00Z"})
    graph.merge_node("Snapshot", "snapshot:pm-loose", {"run_id": "pm-loose"})
    graph.merge_node("PMRun", "pm-early", {"created_at": "2026-09-25T22:00:00Z"})
    early = graph.merge_node("Snapshot", "snapshot:pm-early", {"run_id": "pm-early"})
    monitor = graph.get_node("MonitorRun", "monitorrun:sched-2026-09-25")
    assert monitor is not None
    graph.add_edge(monitor, early, "REPORTED_BY")
    add_fill(graph, "abt", **_FILLED, broker_status_refreshed_at="2026-09-25T10:00Z")

    brief = brief_lines(graph)

    assert brief[1] == f"Equity $101,976.32 ({MINUS}$24.40 since sched-2026-09-24)"
    assert brief[4] == "Filled: BUY 10 ABT"


@pytest.mark.parametrize(
    "earlier",
    [
        None,
        metrics_with(None),
        metrics_with(performance(0.0, sessions=0.0)),
        metrics_with("not a group"),
        "not a mapping",
    ],
    ids=["no-run", "no-group", "zero-sessions", "bad-group", "bad-metrics"],
)
def test_no_reference_figure_reads_no_earlier_figure(earlier: object) -> None:
    """DSP-OUT-06: a reference without a measured figure is never read as zero."""
    graph = InMemoryGraphStore()
    if earlier is not None:
        seed_run(graph, PREVIOUS_DAY, pm_created="2026-09-24T22:40Z", metrics=earlier)
    seed_run(graph, pm_created="2026-09-25T22:41:00+00:00")
    add_fill(graph, "old", **_FILLED, broker_status_refreshed_at="2026-01-02T10:00Z")

    brief = brief_lines(graph)

    assert brief[1] == "Equity $101,976.32 (no earlier figure)"
    assert brief[4] == ("Filled: none" if earlier else "Filled: BUY 10 OLD")
