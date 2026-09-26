"""S234 daily brief at the edges of a fire: the window, skips, bad data, broken parts.

Agent: orchestration
Role: prove no brief failure, bad fact or missing module reaches placement.
External I/O: none; Telegram is injected.
"""

from __future__ import annotations

import sys
from datetime import date
from typing import TYPE_CHECKING

import pytest

from kernel import InMemoryGraphStore
from orchestration.tests.daily_brief_fixtures import (
    PREVIOUS_DAY,
    at,
    fire,
    metrics_with,
    performance,
    seed_run,
)
from orchestration.tests.daily_brief_scenarios import (
    amount_free,
    fault_text,
    run_request,
    seed_pair,
)
from orchestration.tests.scheduled_dispatch_human_helpers import FakeTelegram, preflight

if TYPE_CHECKING:
    from collections.abc import Mapping

    from kernel import Node

_SATURDAY = date(2026, 9, 26)


def test_a4_the_brief_survives_the_windows_early_return() -> None:
    """DSP-TRG-03 / DSP-PERF-01 / DSP-IDN-04: a 23:30 fire briefs and decides nothing.

    Past `_ACT_BY` the fire returns before placement; the brief step sits before
    that return, and the fire's result is exactly its result with no brief due. The
    only change to the graph is the three marker properties on the run's own
    RunRequest: the brief reports and touches no other fact.
    """
    no_brief = InMemoryGraphStore()
    seed_pair(no_brief, briefed=True)
    graph = InMemoryGraphStore()
    seed_pair(graph)
    before = {key: dict(node.props) for key, node in graph._nodes.items()}
    telegram = FakeTelegram()

    result = fire(graph, telegram, at(23, 30))

    after = {key: dict(node.props) for key, node in graph._nodes.items()}
    assert len(telegram.briefs) == 1
    assert result == fire(no_brief, FakeTelegram(), at(23, 30))
    assert result.action == "skipped"
    changed = {key for key in after if after[key] != before.get(key)}
    assert changed == {("RunRequest", "run-request:sched-2026-09-25")}
    added = (
        after[("RunRequest", "run-request:sched-2026-09-25")].keys()
        - before[("RunRequest", "run-request:sched-2026-09-25")].keys()
    )
    assert added == {"brief_sent_at", "brief_message_id", "brief_verdict"}


def test_a5_no_brief_for_a_skipped_or_a_never_placed_run() -> None:
    """DSP-TRG-02 / DSP-TRG-03 / DSP-IDN-04: a skip and an unplaced hold stay silent.

    The Saturday run carries a finished chain, so only the order of the fire (the
    calendar skip first) keeps it silent. The held day has no RunRequest; its hold
    notice has already told the operator.
    """
    skipped = InMemoryGraphStore()
    seed_run(skipped, _SATURDAY, pm_created="2026-09-26T22:41:00+00:00")
    held = InMemoryGraphStore()
    preflight(held, passed=False, checked_at=at(22, 25))
    telegram = FakeTelegram()

    result = fire(skipped, telegram, at(22, 50, _SATURDAY), day=_SATURDAY)
    fire(held, telegram, at(22, 30))
    fire(held, telegram, at(23, 50))

    assert result.action == "skipped"
    assert telegram.briefs == []
    assert len(telegram.sent) == 1


@pytest.mark.parametrize(
    "metrics",
    ["not a mapping", metrics_with({**performance(1.0), "equity_cents": "1.0"})],
    ids=["metrics-not-a-mapping", "equity-not-a-number"],
)
def test_a7_a_malformed_snapshot_is_a_fault_and_nothing_else(metrics: object) -> None:
    """DSP-FAIL-03 / DSP-SEC-02: a compose failure is a fault, with no amount in it.

    Nothing is sent, no marker is written, and placement returns exactly what it
    returns with no brief due.
    """
    no_brief = InMemoryGraphStore()
    seed_pair(no_brief, briefed=True)
    graph = InMemoryGraphStore()
    seed_run(graph, pm_created="2026-09-25T22:41:00+00:00", metrics=metrics)
    preflight(graph, passed=True, checked_at=at(22, 45))
    telegram = FakeTelegram()

    result = fire(graph, telegram, at(22, 50))

    assert telegram.briefs == []
    (fault,) = graph.list_nodes("Fault")
    assert "daily brief not sent for sched-2026-09-25" in str(fault.props["message"])
    assert amount_free(fault_text(fault))
    assert "brief_sent_at" not in run_request(graph).props
    assert result == fire(no_brief, FakeTelegram(), at(22, 50))


def test_a_missing_brief_module_is_a_fault_and_the_fire_places(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DSP-FAIL-03: the brief is imported inside its boundary, so a module the
    image lacks is a fault and the fire still places (DL-218's failure, contained).
    """
    monkeypatch.setitem(sys.modules, "orchestration.daily_brief", None)
    graph = InMemoryGraphStore()
    seed_pair(graph)

    result = fire(graph, FakeTelegram(), at(22, 50))

    assert result.action == "placed"
    (fault,) = graph.list_nodes("Fault")
    assert fault.props["message"] == (
        "daily brief not sent for sched-2026-09-25: brief failed (ModuleNotFoundError)"
    )


class _FaultRefusingGraph(InMemoryGraphStore):
    def merge_node(
        self,
        label: str,
        key: str,
        props: Mapping[str, object],
        *,
        schema_version: int = 1,
    ) -> Node:
        if label == "Fault":
            raise OSError("the spine refused the write")
        return super().merge_node(label, key, props, schema_version=schema_version)


def test_a_fault_the_graph_refuses_still_never_stops_the_fire(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """DSP-FAIL-03: when even the fault cannot be written, the fire still places.

    One stderr line names the error type, and nothing else.
    """
    graph = _FaultRefusingGraph()
    seed_pair(graph)

    result = fire(graph, FakeTelegram(brief_raises=True), at(22, 50))

    assert result.action == "placed"
    err = capsys.readouterr().err
    assert err == "error daily brief fault not recorded: OSError\n"
    assert amount_free(err)


def test_a_refire_for_a_past_session_briefs_nothing() -> None:
    """DSP-TRG-03: a fire briefs its own UTC day only (DL-231, decision 6).

    Functionality checks fire `--as-of` a past session; its finished, unmarked run
    must not be briefed by that fire.
    """
    graph = InMemoryGraphStore()
    seed_run(graph, PREVIOUS_DAY, pm_created="2026-09-24T22:40:00+00:00")
    telegram = FakeTelegram()

    fire(graph, telegram, at(23, 30), day=PREVIOUS_DAY)

    assert telegram.briefs == []
    assert graph.list_nodes("Fault") == ()
