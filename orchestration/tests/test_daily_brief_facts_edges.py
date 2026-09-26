"""S234 fact selection at its edges: needs-you, missing figures, bad facts, no stages.

Agent: orchestration
Role: prove each line says what its owner stored, or that it has nothing to say.
External I/O: none.
"""

from __future__ import annotations

import pytest

from kernel import InMemoryGraphStore
from orchestration.daily_brief_text import BriefDataError
from orchestration.start import place_run_request
from orchestration.tests.daily_brief_fixtures import (
    DAY,
    metrics_with,
    order,
    performance,
    pm_key,
    seed_run,
)
from orchestration.tests.daily_brief_scenarios import add_fill, brief_lines

_CREATED = "2026-09-25T22:41:00+00:00"


def test_a12_needs_you_is_what_health_counts_and_degraded_says_so() -> None:
    """DSP-OUT-06: needs-you is `compute_health`'s count; a degraded run says so.

    Two live error Faults are two open incidents (a warning is not); one unresolved
    critical Flag is one flag (a resolved one is not).
    """
    graph = InMemoryGraphStore()
    seed_run(graph, pm_created=_CREATED, degraded=True)
    for key, severity in (("1", "error"), ("2", "critical"), ("3", "warning")):
        graph.merge_node(
            "Fault",
            f"fault:{key}",
            {"severity": severity, "occurred_at": f"2026-09-25T22:0{key}:00+00:00"},
        )
    graph.merge_node("Flag", "flag:open", {"severity": "critical", "subject_ref": "a"})
    graph.merge_node("Flag", "flag:done", {"severity": "critical", "subject_ref": "b"})
    graph.merge_node(
        "FlagResolution", "resolution:b", {"subject_ref": "b", "severity": "critical"}
    )

    brief = brief_lines(graph)

    assert (
        brief[0] == "\U0001f7e2 PASS · sched-2026-09-25 · Sat 26 Sep 08:50 · degraded"
    )
    assert brief[-1] == "Needs you: 2 open incidents · 1 critical flag"


@pytest.mark.parametrize(
    "metrics",
    [metrics_with(None), metrics_with(performance(0.0, sessions=0.0))],
    ids=["reported-before-the-scoreboard", "reporter-contained-failure"],
)
def test_this_runs_missing_figure_prints_no_amount(metrics: object) -> None:
    """DSP-OUT-06: this run's report without a figure says so; never shows $0.00."""
    graph = InMemoryGraphStore()
    seed_run(graph, pm_created=_CREATED, metrics=metrics)

    assert brief_lines(graph)[1] == "Equity: not in this run's report"


@pytest.mark.parametrize(
    ("clause", "line"),
    [
        (
            "Performance: no usable sessions since 2026-08-01 (inputs unavailable)",
            "Performance: no usable sessions since 2026-08-01 (inputs unavailable)",
        ),
        ("report degraded: graph read failed", "Scoreboard: not in this run's report"),
    ],
    ids=["reporter-says-no-sessions", "no-clause"],
)
def test_the_scoreboard_is_the_reporters_clause_as_stored(
    clause: str, line: str
) -> None:
    """DSP-OUT-06: the vs-SPY line is cut from `headline_summary`, never recomputed."""
    graph = InMemoryGraphStore()
    seed_run(graph, pm_created=_CREATED, clause=clause)

    assert brief_lines(graph)[2] == line


def test_unreadable_facts_are_named_data_errors_not_guesses() -> None:
    """DSP-FAIL-03: a missing PM time or a malformed order raises a named error.

    The error names the field and never its value, so its fault carries no amount.
    """
    no_time = InMemoryGraphStore()
    seed_run(no_time, pm_created="not a time")
    no_ticker = InMemoryGraphStore()
    seed_run(no_ticker, pm_created=_CREATED)
    add_fill(no_ticker, "x", ticker="", source_run_id=pm_key(DAY))
    flag_quantity = InMemoryGraphStore()
    seed_run(flag_quantity, pm_created=_CREATED)
    add_fill(flag_quantity, "y", quantity=True, source_run_id=pm_key(DAY))

    with pytest.raises(BriefDataError, match=r"^PMRun\.created_at$"):
        brief_lines(no_time)
    with pytest.raises(BriefDataError, match=r"^Fill\.ticker$"):
        brief_lines(no_ticker)
    with pytest.raises(BriefDataError, match=r"^Fill\.quantity$"):
        brief_lines(flag_quantity)


def test_a_red_brief_names_the_stage_and_what_the_run_ordered() -> None:
    """DSP-TRG-03 / DSP-OUT-06: RED names the last stage finished, or none.

    A run stopped after execution lists the orders it placed; a run with only its
    RunRequest says no stage finished.
    """
    bare = InMemoryGraphStore()
    place_run_request(bare, run_id="sched-2026-09-25", tickers=("AAPL",), as_of=DAY)
    ordered = InMemoryGraphStore()
    seed_run(
        ordered,
        pm_created=_CREATED,
        through="ExecutionRun",
        approved=(order("BMY", 16, "61.82"),),
    )
    limit = {"order_applied_limit_price_cents": 6182}
    add_fill(ordered, "bmy", quantity=16, source_run_id=pm_key(DAY), **limit)

    assert brief_lines(bare) == [
        "\U0001f534 NOT FINISHED · sched-2026-09-25 · Sat 26 Sep 08:50",
        "No stage finished",
        "Orders: none",
        "Needs you: nothing",
    ]
    assert brief_lines(ordered)[1:3] == [
        "Last stage finished: execution",
        "Orders: BUY 16 BMY ≤ $61.82",
    ]
