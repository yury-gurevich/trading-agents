"""Dashboard POST route that appends one operator RunHoldAnswer fact.

Agent: surfaces
Role: validate a dashboard answer against an active dispatcher hold.
External I/O: reads and writes the injected GraphStore.
"""

from __future__ import annotations

import json
from datetime import UTC, date, datetime
from typing import TYPE_CHECKING, Any, cast

from orchestration.fleet_readiness import is_active_run_hold
from orchestration.hold_answers import record_answer

if TYPE_CHECKING:
    from kernel import GraphStore
    from orchestration.hold_answers import Answer

_ANSWERS = frozenset(("run_now", "skip_today"))


def handle_hold_answer(
    environ: dict[str, Any], graph: GraphStore, *, now: datetime | None
) -> tuple[int, dict[str, object]]:
    """Validate a dashboard choice and append the shared answer fact."""
    if environ.get("REQUEST_METHOD") != "POST":
        return 405, {"error": "POST only"}
    payload = _json_body(environ)
    run_id, answer = payload.get("run_id"), payload.get("answer")
    if not isinstance(run_id, str) or answer not in _ANSWERS:
        return 400, {"error": "run_id and answer are required"}
    hold = next(
        (
            node
            for node in graph.list_nodes("RunHold")
            if node.props.get("run_id") == run_id
            and is_active_run_hold(node)
            and "answered_with" not in node.props
        ),
        None,
    )
    if hold is None:
        return 404, {"error": "no active hold"}
    answered_at = now or datetime.now(tz=UTC)
    record_answer(
        graph,
        run_id=run_id,
        as_of=_as_of(hold.props.get("as_of"), answered_at.date()),
        answer=cast("Answer", answer),
        source="dashboard",
        answered_at=answered_at,
        update_id=0,
    )
    return 200, {"run_id": run_id, "answer": answer}


def _json_body(environ: dict[str, Any]) -> dict[str, object]:
    try:
        size = int(str(environ.get("CONTENT_LENGTH", "0")))
        value = json.loads(environ["wsgi.input"].read(max(size, 0)) or b"{}")
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _as_of(raw: object, fallback: date) -> date:
    try:
        return date.fromisoformat(str(raw))
    except ValueError:
        return fallback
