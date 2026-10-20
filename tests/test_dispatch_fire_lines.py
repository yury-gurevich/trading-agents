"""Sprint 285: job lines describe real fires and their window.

Agent: tooling
Role: prove the job's public result rendering and last-fire time budget.
External I/O: reads the deploy script as text; all fires use in-memory ports.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import get_args, get_type_hints

from scripts.dispatch_scheduled_run import format_dispatch_result

from kernel import InMemoryGraphStore
from orchestration.scheduled_dispatch import ScheduledDispatchResult
from orchestration.scheduled_dispatch_actions import _ACT_BY
from orchestration.tests.scheduled_dispatch_human_helpers import (
    FakeAnswer,
    FakeTelegram,
)
from orchestration.tests.test_scheduled_dispatch_once import RUN_ID, at, check, fire


def test_each_fire_prints_what_it_did() -> None:
    """DSP-OBS-04: exact lines distinguish each action and both window sides."""
    ready, held, empty = (InMemoryGraphStore() for _ in range(3))
    telegram = FakeTelegram()
    check(ready, passed=True)
    check(held)
    results = [
        fire(ready, telegram, at(22, 20)),
        fire(ready, telegram, at(22, 30)),
        fire(ready, telegram, at(23, 50)),
        fire(held, telegram, at(22, 30)),
        fire(held, telegram, at(23, 20)),
        fire(empty, telegram, at(23, 20)),
    ]
    assert [format_dispatch_result(result) for result in results] == [
        "skipped sched-2026-10-19 reason=before the placing window, 22:30 to 23:10 UTC",
        "placed sched-2026-10-19 reason=NYSE trading session",
        "already-placed sched-2026-10-19 reason=placed by an earlier fire",
        "held sched-2026-10-19 reason=failing failures=1",
        "held sched-2026-10-19 reason=after the placing window, "
        "22:30 to 23:10 UTC failures=1",
        "skipped sched-2026-10-19 reason=after the placing window, 22:30 to 23:10 UTC",
    ]


def test_a_skip_answer_still_says_operator() -> None:
    """DSP-OBS-04 / DSP-OUT-02: Skip today keeps its operator reason and no run."""
    graph, telegram = InMemoryGraphStore(), FakeTelegram()
    check(graph)
    fire(graph, telegram, at(22, 30))
    before = graph.list_nodes("RunHold")
    telegram.answers = (FakeAnswer(3, "skip_today", RUN_ID, "callback-3"),)
    result = fire(graph, telegram, at(22, 40))
    assert format_dispatch_result(result) == "skipped sched-2026-10-19 reason=operator"
    assert graph.list_nodes("RunRequest") == ()
    assert [h.key for h in graph.list_nodes("RunHold")] == [h.key for h in before]


def test_the_result_names_one_of_four_actions_and_readiness_only_when_held() -> None:
    """DSP-TYP-01: four literal actions and readiness only on an in-window hold."""
    assert get_args(get_type_hints(ScheduledDispatchResult)["action"]) == (
        "placed",
        "already-placed",
        "skipped",
        "held",
    )
    graph, telegram = InMemoryGraphStore(), FakeTelegram()
    check(graph)
    results = [fire(graph, telegram, at(22, minute)) for minute in (20, 30)]
    check(graph, passed=True, now=at(22, 31, 5))
    results += [fire(graph, telegram, at(22, minute)) for minute in (40, 50)]
    assert [r.action for r in results] == [
        "skipped",
        "held",
        "placed",
        "already-placed",
    ]
    assert [r.readiness_state for r in results] == [None, "failing", None, None]


def test_a_run_placed_at_the_last_fire_ends_before_the_window() -> None:
    """DSP-TRG-01: the latest fitting ten-minute tick leaves twenty minutes."""
    text = (Path(__file__).resolve().parents[1] / "infra/deploy-agents.ps1").read_text(
        encoding="utf-8"
    )
    match = re.search(r"\[string\]\$ScaleEnd\s*=\s*'([0-9]+) ([0-9]+) \* \* 1-5'", text)
    assert match is not None
    minute, hour = map(int, match.groups())
    end = datetime(2026, 10, 19, hour, minute, tzinfo=UTC)
    last = datetime.combine(end.date(), _ACT_BY, UTC)
    assert last + timedelta(minutes=20) <= end
    assert last + timedelta(minutes=30) > end
