"""The fault boundary around the daily brief: a brief can only ever become a fault.

Agent: orchestration
Role: attempt the brief so no failure, amount or missing module can reach placement.
External I/O: imports and calls the brief step; writes Fault nodes to the injected
    GraphStore, and one stderr line only when even that write fails.

`scheduled_dispatch_human` imports this module and nothing else of the brief. The
brief itself is imported inside the `try` below, so a module the image lacks, or
one that fails at import, is a fault and the fire goes on to place (`DSP-FAIL-03`).
A fault names the step and an error type, never a value (`DSP-SEC-02`).
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from kernel import CollectingFaultSink, GraphFaultSink
from kernel.errors import fault_boundary
from orchestration.settings import OrchestratorSettings

if TYPE_CHECKING:
    from datetime import date, datetime

    from kernel import GraphStore
    from orchestration.telegram_port import TelegramPort


class DailyBriefNotSentError(RuntimeError):
    """A daily brief was not sent; the message names the step and error type only."""


def brief_safely(
    graph: GraphStore,
    telegram: TelegramPort,
    *,
    run_id: str,
    as_of: date,
    now: datetime,
    settings: OrchestratorSettings | None,
) -> None:
    """Attempt today's brief; any failure becomes one Fault and the fire goes on."""
    try:
        from orchestration.daily_brief import attempt_brief

        timezone = (settings or OrchestratorSettings()).operator_timezone
        failure = attempt_brief(
            graph, telegram, run_id=run_id, as_of=as_of, now=now, timezone=timezone
        )
    except Exception as exc:  # the boundary itself: a type name, never a message
        failure = f"brief failed ({type(exc).__name__})"
    if failure is not None:
        _record(graph, f"daily brief not sent for {run_id}: {failure}")


def _record(graph: GraphStore, message: str) -> None:
    # Raised outside any `except`, so the Fault's traceback chains no earlier error.
    try:
        with fault_boundary(
            GraphFaultSink(graph, CollectingFaultSink()),
            agent="orchestration",
            module="orchestration.daily_brief",
            capability="daily_brief",
            reraise=False,
        ):
            raise DailyBriefNotSentError(message)
    except Exception as exc:  # the graph refused the fault itself
        sys.stderr.write(
            f"error daily brief fault not recorded: {type(exc).__name__}\n"
        )
