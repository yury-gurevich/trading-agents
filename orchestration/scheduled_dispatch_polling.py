"""Fault-tolerant Telegram answer polling for one scheduled dispatcher fire.

Agent: orchestration
Role: append valid answers and confirm Telegram's update cursor.
External I/O: calls the injected Telegram port and writes the injected GraphStore.
"""

from __future__ import annotations

from datetime import date
from functools import partial
from typing import TYPE_CHECKING

from kernel import CollectingFaultSink, GraphFaultSink
from kernel.errors import fault_boundary
from orchestration.hold_answers import record_answer

if TYPE_CHECKING:
    from collections.abc import Callable
    from datetime import datetime

    from kernel import GraphStore
    from orchestration.telegram_port import TelegramPort
    from orchestration.telegram_updates import TelegramAnswer


def poll_answers(
    graph: GraphStore, telegram: TelegramPort, *, as_of: date, now: datetime
) -> None:
    """Write valid callback answers and clear only the handled update range."""
    empty_answers: tuple[TelegramAnswer, ...] = ()
    answers = fault_safe(graph, telegram, telegram.poll_answers, empty_answers)
    highest = 0
    for answer in answers:
        if record_answer(
            graph,
            run_id=answer.run_id,
            as_of=answer_as_of(answer.run_id, as_of),
            answer=answer.answer,
            source="telegram",
            answered_at=now,
            update_id=answer.update_id,
        ):
            acknowledge = partial(
                telegram.ack_button,
                callback_query_id=answer.callback_query_id,
                text="Answer recorded",
            )
            fault_safe(
                graph,
                telegram,
                acknowledge,
                False,
            )
            highest = max(highest, answer.update_id)
    if highest:
        fault_safe(
            graph, telegram, lambda: telegram.confirm(up_to_update_id=highest), False
        )


def answer_as_of(run_id: str, fallback: date) -> date:
    """Return the scheduled day encoded in a run id, when it is valid."""
    try:
        return date.fromisoformat(run_id.removeprefix("sched-"))
    except ValueError:
        return fallback


def fault_safe[T](
    graph: GraphStore,
    telegram: TelegramPort,
    operation: Callable[[], T],
    fallback: T,
) -> T:
    """Convert Telegram failures into durable faults and a caller-selected fallback."""
    try:
        result = operation()
    except Exception as exc:
        _record_fault(graph, exc)
        return fallback
    if error := getattr(telegram, "last_error", ""):
        _record_fault(graph, RuntimeError(str(error)))
        return fallback
    return result


def _record_fault(graph: GraphStore, error: Exception) -> None:
    sink = GraphFaultSink(graph, CollectingFaultSink())
    with fault_boundary(
        sink,
        agent="orchestration",
        module="orchestration.scheduled_dispatch_human",
        capability="telegram",
        reraise=False,
    ):
        raise error
