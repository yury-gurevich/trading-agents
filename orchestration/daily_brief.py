"""The daily brief: which fire sends it, and the once-per-run marker it leaves.

Agent: orchestration
Role: brief today's scheduled run once its Snapshot exists, or RED on the last fire.
External I/O: reads/writes the injected GraphStore and calls the injected Telegram port.

Imported only inside `daily_brief_guard`'s fault boundary, so neither this module
nor anything it imports can stop a dispatcher fire (`DSP-FAIL-03`).
"""

from __future__ import annotations

from datetime import UTC, time
from typing import TYPE_CHECKING

from contracts.provider import RUN_REQUEST_LABEL
from orchestration.batch_chain import walk_chain
from orchestration.daily_brief_facts import brief_facts
from orchestration.daily_brief_text import BriefDataError, compose_brief

if TYPE_CHECKING:
    from datetime import date, datetime

    from kernel import GraphStore
    from orchestration.telegram_port import TelegramPort

# The dispatcher cron `*/10 22-23 * * 1-5` (UTC) fires last at 23:50. A run with no
# Snapshot by then gets its RED brief from that fire: no later fire will see it.
LAST_FIRE = time(23, 50)
BRIEF_SENT_AT = "brief_sent_at"


def attempt_brief(
    graph: GraphStore,
    telegram: TelegramPort,
    *,
    run_id: str,
    as_of: date,
    now: datetime,
    timezone: str,
) -> str | None:
    """Send today's brief when it is due; return why it was not sent, else None."""
    fired = now.astimezone(UTC)
    if as_of != fired.date():  # a re-fire for a past session briefs nothing
        return None
    request = graph.get_node(RUN_REQUEST_LABEL, f"run-request:{run_id}")
    if request is None or BRIEF_SENT_AT in request.props:
        return None
    nodes = walk_chain(graph, run_id)
    if "Snapshot" not in nodes and fired.time() < LAST_FIRE:
        return None
    try:
        facts = brief_facts(graph, run_id, nodes, now=now, timezone=timezone)
    except BriefDataError as exc:
        return f"compose failed ({exc})"  # names a field, never its value
    text = compose_brief(facts)
    try:
        message_id = telegram.send_brief(text=text)
    except Exception as exc:  # the port's text may quote the brief: keep the type only
        return f"send failed ({type(exc).__name__})"
    if message_id is None:
        return f"send failed ({_port_error(telegram)})"
    graph.merge_node(
        RUN_REQUEST_LABEL,
        request.key,
        {
            BRIEF_SENT_AT: now.isoformat(timespec="seconds"),
            "brief_message_id": message_id,
            "brief_verdict": facts.verdict,
        },
    )
    return None


def preview_brief(
    graph: GraphStore, run_id: str, *, now: datetime, timezone: str
) -> str | None:
    """Return the text a fire would send for ``run_id`` now; send and write nothing."""
    nodes = walk_chain(graph, run_id)
    if not nodes:
        return None
    return compose_brief(brief_facts(graph, run_id, nodes, now=now, timezone=timezone))


def _port_error(telegram: TelegramPort) -> str:
    """The port's own error word; anything else might carry text, so it is dropped."""
    error = str(getattr(telegram, "last_error", "") or "")
    return error if error.isidentifier() else "no message id"
