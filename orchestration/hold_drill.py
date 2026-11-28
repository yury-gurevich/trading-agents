"""Hold drill: the dispatcher's own fire holds a past session and acts on the press.

Agent: orchestration
Role: stage work-queue 120 (a) (DL-330): on an in-memory graph, plant a failing
      fleet preflight for a past NYSE session, fire the unchanged
      dispatch_with_human_answer at a planted clock inside the placing window, and
      wait for the operator's press on the test bot; the verdict module judges it.
External I/O: the injected Telegram port (the test bot); the sleep it is handed.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, time, timedelta
from typing import TYPE_CHECKING

from agents.provider.domain.market_calendar import is_trading_session
from kernel import InMemoryGraphStore
from orchestration.hold_drill_verdict import faults, judge, verdict
from orchestration.scheduled_dispatch import scheduled_run_id
from orchestration.scheduled_dispatch_human import dispatch_with_human_answer

if TYPE_CHECKING:
    from collections.abc import Callable
    from datetime import date

    from kernel import GraphStore
    from orchestration.hold_answers import Answer
    from orchestration.scheduled_dispatch import ScheduledDispatchResult
    from orchestration.settings import OrchestratorSettings
    from orchestration.telegram_port import TelegramPort

ROUNDS: tuple[Answer, ...] = ("run_now", "skip_today")
BUTTON = {"run_now": "Run now", "skip_today": "Skip today"}
DRILL_FAILURE = "transient:execution:alpaca-broker:hold-drill"
PREFLIGHT_AT = time(22, 25)  # fresh at both fires: 70 minutes is the age limit
FIRST_FIRE = time(22, 30, 5)  # the first tick of the placing window, 22:30 to 23:10
ANSWER_FIRE = time(22, 40, 5)


@dataclass(frozen=True)
class Drill:
    """What every round shares: the bot, the settings, the waiting and the printer."""

    telegram: TelegramPort
    settings: OrchestratorSettings
    poll_seconds: int
    wait_seconds: int
    sleep: Callable[[float], None]
    report: Callable[[str], None]


def prior_sessions(today: date, count: int) -> tuple[date, ...]:
    """Return the *count* NYSE sessions before *today*, newest first."""
    found: list[date] = []
    day = today
    while len(found) < count:
        day -= timedelta(days=1)
        if is_trading_session(day):
            found.append(day)
    return tuple(found)


def run_drill(drill: Drill, *, today: date) -> tuple[bool, ...]:
    """Run one round per answer, Run now first, each on its own past session."""
    sessions = prior_sessions(today, len(ROUNDS))
    passed = tuple(
        run_round(drill, as_of=as_of, wanted=wanted)
        for wanted, as_of in zip(ROUNDS, sessions, strict=True)
    )
    drill.telegram.send_brief(
        text=f"Hold drill done: {sum(passed)} of 2 rounds passed."
    )
    return passed


def run_round(drill: Drill, *, as_of: date, wanted: Answer) -> bool:
    """Hold *as_of*'s run, ask for *wanted*, and judge what came back."""
    graph = InMemoryGraphStore()
    run_id = scheduled_run_id(as_of)
    _drain(drill.telegram)
    graph.merge_node(
        "FleetPreflight",
        "preflight:hold-drill",
        {
            "checked_at": datetime.combine(as_of, PREFLIGHT_AT, UTC).isoformat(),
            "passed": False,
            "failures": [DRILL_FAILURE],
        },
    )
    button = BUTTON[wanted]
    drill.telegram.send_brief(
        text=f"Hold drill: nothing in the fleet is held. Next message: press {button}."
    )
    result = _fire(drill, graph, as_of, FIRST_FIRE)
    hold = graph.get_node("RunHold", result.node_key or "")
    if hold is None or "notified_at" not in hold.props:
        line = f"notice not sent ({result.action}){faults(graph)}"
        return verdict(drill.report, run_id, passed=False, lines=[line])
    drill.report(f"{run_id}  held, notice {hold.props['notice_message_id']}: {button}")
    waited = 0
    while (result := _fire(drill, graph, as_of, ANSWER_FIRE)).action == "held":
        if waited >= drill.wait_seconds:
            line = f"no answer in {waited} s"
            return verdict(drill.report, run_id, passed=False, lines=[line])
        drill.sleep(drill.poll_seconds)
        waited += drill.poll_seconds
    return judge(
        graph,
        drill.telegram,
        run_id=run_id,
        wanted=wanted,
        result=result,
        report=drill.report,
    )


def _drain(telegram: TelegramPort) -> None:
    """Confirm any press already waiting: only a press after the notice counts."""
    stale = telegram.poll_answers()
    if stale:
        telegram.confirm(up_to_update_id=max(answer.update_id for answer in stale))


def _fire(
    drill: Drill, graph: GraphStore, as_of: date, clock: time
) -> ScheduledDispatchResult:
    now = datetime.combine(as_of, clock, UTC)
    return dispatch_with_human_answer(
        graph, as_of=as_of, now=now, telegram=drill.telegram, settings=drill.settings
    )
