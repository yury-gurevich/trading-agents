"""Human-notified hold handling around scheduled RunRequest placement.

Agent: orchestration
Role: notify one held run and honour its first human answer.
External I/O: reads/writes GraphStore and calls the injected Telegram port.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from contracts.provider import RUN_REQUEST_LABEL
from contracts.run_posture import RUN_POSTURE_DEGRADED
from orchestration.daily_brief_guard import brief_safely
from orchestration.fleet_readiness import is_active_run_hold
from orchestration.hold_answers import effective_answer
from orchestration.scheduled_dispatch import (
    ScheduledDispatchResult,
    decide_scheduled_run,
)
from orchestration.scheduled_dispatch_actions import (
    act_by_text,
    is_action_time,
    outside_window,
    place_override,
    place_scheduled,
)
from orchestration.scheduled_dispatch_polling import fault_safe, poll_answers
from orchestration.settings import OrchestratorSettings

if TYPE_CHECKING:
    from datetime import date, datetime

    from agents.scanner.universe import UniverseSource
    from kernel import GraphStore, Node
    from orchestration.scheduled_dispatch import TradingCalendar
    from orchestration.telegram_port import TelegramPort


def dispatch_with_human_answer(
    graph: GraphStore,
    *,
    as_of: date,
    now: datetime,
    telegram: TelegramPort,
    calendar: TradingCalendar | None = None,
    settings: OrchestratorSettings | None = None,
    universe_source: UniverseSource | None = None,
) -> ScheduledDispatchResult:
    """Run one answer-aware dispatcher fire without changing ready-run semantics."""
    decision = (
        decide_scheduled_run(as_of, calendar=calendar)
        if calendar is not None
        else decide_scheduled_run(as_of)
    )
    if decision.action == "skip":
        return ScheduledDispatchResult("skipped", decision.run_id, decision.reason)
    hold = _active_hold(graph, decision.run_id)
    if hold is not None:
        poll_answers(graph, telegram, as_of=as_of, now=now)
    answer = effective_answer(graph, run_id=decision.run_id)
    if answer is not None:
        _mark_answer(graph, hold, answer)
    brief_safely(
        graph, telegram, run_id=decision.run_id, as_of=as_of, now=now, settings=settings
    )
    if not is_action_time(now):
        return outside_window(decision.run_id, decision.reason, hold)
    if answer == "skip_today":
        return ScheduledDispatchResult("skipped", decision.run_id, "operator")
    if answer == "run_now":
        return place_override(
            graph,
            run_id=decision.run_id,
            as_of=as_of,
            reason=decision.reason,
            settings=settings,
            universe_source=universe_source,
        )
    result = place_scheduled(
        graph,
        as_of=as_of,
        now=now,
        calendar=calendar,
        settings=settings,
        universe_source=universe_source,
    )
    if result.action == "held":
        zone = (settings or OrchestratorSettings()).operator_timezone
        _notify_new_hold(graph, telegram, result, now, zone)
    elif result.action == "placed" and result.run_posture == RUN_POSTURE_DEGRADED:
        _notify_degraded_run(graph, telegram, result, now)
    return result


def _active_hold(graph: GraphStore, run_id: str) -> Node | None:
    return next(
        (
            node
            for node in graph.list_nodes("RunHold")
            if node.props.get("run_id") == run_id and is_active_run_hold(node)
        ),
        None,
    )


def _notify_new_hold(
    graph: GraphStore,
    telegram: TelegramPort,
    result: ScheduledDispatchResult,
    now: datetime,
    timezone: str,
) -> None:
    hold = graph.get_node("RunHold", result.node_key or "")
    if hold is None or "notified_at" in hold.props:
        return
    message_id = fault_safe(
        graph,
        telegram,
        lambda: telegram.send_hold_notice(
            run_id=result.run_id,
            failures=result.failures,
            act_by=act_by_text(now, timezone),
        ),
        None,
    )
    if message_id is not None:
        graph.merge_node(
            "RunHold",
            hold.key,
            {
                "notified_at": now.isoformat(timespec="seconds"),
                "notice_message_id": message_id,
            },
        )


def _notify_degraded_run(
    graph: GraphStore,
    telegram: TelegramPort,
    result: ScheduledDispatchResult,
    now: datetime,
) -> None:
    run = graph.get_node(RUN_REQUEST_LABEL, result.node_key or "")
    if run is None or "degraded_notified_at" in run.props:
        return
    message_id = fault_safe(
        graph,
        telegram,
        lambda: telegram.send_degraded_notice(
            run_id=result.run_id, failures=result.failures
        ),
        None,
    )
    if message_id is not None:
        graph.merge_node(
            RUN_REQUEST_LABEL,
            run.key,
            {
                "degraded_notified_at": now.isoformat(timespec="seconds"),
                "degraded_notice_message_id": message_id,
            },
        )


def _mark_answer(graph: GraphStore, hold: Node | None, answer: str) -> None:
    if hold is not None and "answered_with" not in hold.props:
        graph.merge_node("RunHold", hold.key, {"answered_with": answer})
