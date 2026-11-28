"""Hold-drill verdicts: what one round's press recorded and did, judged against the ask.

Agent: orchestration
Role: judge one hold-drill round (work-queue 120 (a), DL-330): the answer recorded from
      Telegram is the one asked for, the dispatcher acted on it, Telegram's cursor is
      past it, and every fault the fire wrote is printed; then report the verdict.
External I/O: one poll through the injected Telegram port; the printer it is handed.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from contracts.provider import RUN_REQUEST_LABEL

if TYPE_CHECKING:
    from collections.abc import Callable

    from kernel import GraphStore
    from orchestration.hold_answers import Answer
    from orchestration.scheduled_dispatch import ScheduledDispatchResult
    from orchestration.telegram_port import TelegramPort

ACT = {"run_now": "placed", "skip_today": "skipped"}


def judge(
    graph: GraphStore,
    telegram: TelegramPort,
    *,
    run_id: str,
    wanted: Answer,
    result: ScheduledDispatchResult,
    report: Callable[[str], None],
) -> bool:
    """Report one answered round's lines and return whether it did what was asked."""
    answers = [
        n for n in graph.list_nodes("RunHoldAnswer") if n.props.get("run_id") == run_id
    ]
    pressed = str(answers[0].props["answer"]) if answers else "none"
    source = str(answers[0].props["source"]) if answers else "-"
    placed = graph.get_node(RUN_REQUEST_LABEL, f"run-request:{run_id}") is not None
    pending = [a for a in telegram.poll_answers() if a.run_id == run_id]
    asked = f", asked {wanted}" if pressed != wanted else ""
    cursor = f"{len(pending)} answer(s) still pending" if pending else "confirmed"
    lines = [
        f"answer    {pressed} from {source}{asked}",
        f"act       {result.action} reason={result.reason}, RunRequest {int(placed)}",
        f"cursor    {cursor}",
        f"faults    {len(graph.list_nodes('Fault'))}{faults(graph)}",
    ]
    passed = (
        pressed == wanted
        and result.action == ACT[wanted]
        and placed == (wanted == "run_now")
        and not pending
    )
    return verdict(report, run_id, passed=passed, lines=lines)


def faults(graph: GraphStore) -> str:
    """Return every Fault's capability and message, in brackets, or ''."""
    found = [
        f"{n.props.get('capability')}: {n.props.get('message')}"
        for n in graph.list_nodes("Fault")
    ]
    return f" ({'; '.join(found)})" if found else ""


def verdict(
    report: Callable[[str], None], run_id: str, *, passed: bool, lines: list[str]
) -> bool:
    """Print the round's verdict line, then its evidence lines; return *passed*."""
    report(f"{run_id}  {'PASS' if passed else 'FAIL'}")
    for line in lines:
        report(f"  {line}")
    return passed
