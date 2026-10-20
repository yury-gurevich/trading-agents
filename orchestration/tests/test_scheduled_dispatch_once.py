"""Sprint 285: each fire keeps its deadline and places the day once.

Agent: orchestration
Role: prove tick boundaries, placement guards and degraded-notice retries.
External I/O: none; graph, universe and Telegram are in memory.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest

from agents.scanner.universe import FakeUniverse
from kernel import InMemoryGraphStore
from orchestration.scheduled_dispatch_actions import is_action_time
from orchestration.scheduled_dispatch_human import dispatch_with_human_answer
from orchestration.settings import OrchestratorSettings
from orchestration.tests.scheduled_dispatch_human_helpers import (
    FakeAnswer,
    FakeTelegram,
    preflight,
)

if TYPE_CHECKING:
    from kernel import Node
    from orchestration.scheduled_dispatch import ScheduledDispatchResult as Result

RUN_ID = "sched-2026-10-19"
FAILURES = ("unrecoverable:provider:credential",)


def at(hour: int, minute: int, second: int = 26) -> datetime:
    """Land fires 26 seconds after their tick, unless testing an exact boundary."""
    return datetime(2026, 10, 19, hour, minute, second, tzinfo=UTC)


def check(
    graph: InMemoryGraphStore,
    *,
    passed: bool = False,
    now: datetime | None = None,
    failures: tuple[str, ...] = FAILURES,
) -> None:
    """Append a deterministic preflight, with no failures when passing."""
    preflight(
        graph,
        passed=passed,
        checked_at=now or at(22, 0, 45),
        failures=() if passed else failures,
    )


def fire(graph: InMemoryGraphStore, telegram: FakeTelegram, now: datetime) -> Result:
    """Exercise the public fire with local settings and a synthetic universe."""
    return dispatch_with_human_answer(
        graph,
        as_of=now.date(),
        now=now,
        telegram=telegram,
        settings=OrchestratorSettings(_env_file=None),
        universe_source=FakeUniverse({"sp500": ("AAPL",)}),
    )


class _ReadGraph(InMemoryGraphStore):
    """Count both readiness lookup paths around complete fires."""

    readiness_reads = 0

    def list_nodes(self, label: str) -> tuple[Node, ...]:
        self.readiness_reads += label == "FleetPreflight"
        return super().list_nodes(label)

    def get_node(self, label: str, key: str) -> Node | None:
        self.readiness_reads += label == "FleetPreflight"
        return super().get_node(label, key)


def test_a_night_places_the_run_once_and_every_later_fire_says_so() -> None:
    """DSP-OBS-04 / DSP-IDM-02: twelve real fires place once and name each outcome."""
    graph, telegram = InMemoryGraphStore(), FakeTelegram()
    check(graph, passed=True)
    results = [fire(graph, telegram, at(22 + n // 6, n % 6 * 10)) for n in range(12)]
    assert [(r.action, r.reason) for r in results] == (
        [("skipped", "before the placing window, 22:30 to 23:10 UTC")] * 3
        + [("placed", "NYSE trading session")]
        + [("already-placed", "placed by an earlier fire")] * 8
    )
    assert len(graph.list_nodes("RunRequest")) == 1
    assert graph.list_nodes("RunHold") == ()


def test_a_placed_run_is_never_held_when_a_later_check_fails() -> None:
    """DSP-NEV-04: a placed run causes no readiness read, hold or hold notice."""
    graph, telegram = _ReadGraph(), FakeTelegram()
    check(graph, passed=True)
    assert fire(graph, telegram, at(22, 30)).action == "placed"
    check(graph, now=at(23, 1, 5))
    before = graph.readiness_reads
    results = [fire(graph, telegram, at(23, minute)) for minute in (10, 20)]
    assert graph.readiness_reads == before
    assert [r.action for r in results] == ["already-placed", "already-placed"]
    assert graph.list_nodes("RunHold") == ()
    assert telegram.sent == []


@pytest.mark.parametrize(
    ("clock", "expected"),
    [
        ("22:29:59", False),
        ("22:30:00", True),
        ("23:10:26", True),
        ("23:10:59", True),
        ("23:19:59", True),
        ("23:20:00", False),
        ("23:20:26", False),
    ],
)
def test_the_last_placing_fire_is_the_2310_tick(
    clock: str,
    expected: bool,
) -> None:
    """DSP-TRG-01: the fire belongs to its ten-minute tick, including seconds."""
    assert (
        is_action_time(datetime.fromisoformat(f"2026-10-19T{clock}+00:00")) is expected
    )


@pytest.mark.parametrize(
    "late_answer", [False, True], ids=["2310-release", "2320-answer"]
)
def test_a_held_run_released_at_the_2310_fire_is_placed_and_at_2320_is_not(
    late_answer: bool,
) -> None:
    """DSP-TRG-01 / DSP-PERF-01: release fits 23:10; a late answer is evidence only."""
    graph, telegram = InMemoryGraphStore(), FakeTelegram()
    check(graph)
    assert fire(graph, telegram, at(22, 30)).action == "held"
    if late_answer:
        telegram.answers = (FakeAnswer(1, "run_now", RUN_ID, "callback-1"),)
        result = fire(graph, telegram, at(23, 20))
        assert result.action == "held"
        assert result.reason == "after the placing window, 22:30 to 23:10 UTC"
        assert result.failures == FAILURES
        assert graph.list_nodes("RunRequest") == ()
        (hold,) = graph.list_nodes("RunHold")
        assert hold.props["answered_with"] == "run_now"
    else:
        check(graph, passed=True, now=at(23, 1, 5))
        assert fire(graph, telegram, at(23, 10)).action == "placed"
        (hold,) = graph.list_nodes("RunHold")
        assert hold.props["released_at"] == at(23, 10).isoformat(timespec="seconds")


def test_the_hold_notice_names_the_2310_deadline() -> None:
    """DSP-OBS-02 / DSP-TRG-01: the notice promises the actual last placing tick."""
    graph, telegram = InMemoryGraphStore(), FakeTelegram()
    check(graph)
    fire(graph, telegram, at(22, 30))
    assert telegram.sent[0]["act_by"] == "10:10 Melbourne (23:10 UTC)"


def test_an_override_placed_run_is_already_placed_at_the_next_fire() -> None:
    """DSP-NEV-04 / DSP-IDM-02: Run now places once even with a persistent failure."""
    graph, telegram = InMemoryGraphStore(), FakeTelegram()
    check(graph)
    fire(graph, telegram, at(22, 30))
    telegram.answers = (FakeAnswer(2, "run_now", RUN_ID, "callback-2"),)
    assert fire(graph, telegram, at(22, 40)).action == "placed"
    assert fire(graph, telegram, at(22, 50)).action == "already-placed"
    assert len(graph.list_nodes("RunRequest")) == 1


@pytest.mark.parametrize(("now", "retried"), [(at(22, 40), True), (at(23, 20), False)])
def test_an_unsent_degraded_notice_is_retried_inside_the_window_only(
    now: datetime,
    retried: bool,
) -> None:
    """DSP-OUT-05 / DSP-NEV-04: preserve degraded causes and retry only in-window."""
    graph, telegram = InMemoryGraphStore(), FakeTelegram(degraded_returns_none=True)
    failures = ("unrecoverable:operator:anthropic:unrecoverable:http_400",)
    check(graph, failures=failures)
    assert fire(graph, telegram, at(22, 30)).action == "placed"
    (run,) = graph.list_nodes("RunRequest")
    assert "degraded_notified_at" not in run.props
    telegram.degraded_returns_none = False
    result = fire(graph, telegram, now)
    assert result.action == "already-placed"
    assert result.run_posture == "degraded"
    assert result.failures == failures
    assert len(telegram.degraded_sent) == 1 + retried
    (run,) = graph.list_nodes("RunRequest")
    notified = run.props.get("degraded_notified_at")
    assert notified == (now.isoformat(timespec="seconds") if retried else None)
    assert graph.list_nodes("RunHold") == ()
    assert telegram.sent == []
