"""Operator chat request adapter for the operations dashboard.

Agent: surfaces
Role: validate one chat turn and expose the existing bounded surface tools.
External I/O: operator and supervisor calls through the injected SurfaceContext.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from surfaces.mcp_tools import dispatch_tool

if TYPE_CHECKING:
    from surfaces.context import SurfaceContext

_NOT_CONNECTED = "chat is not connected on this deployment"
_QUICK_TOOLS = {
    "explain this run": "explain",
    "system status": "status",
    "open incidents": "incidents",
}


def handle_chat(
    environ: dict[str, Any], context: SurfaceContext | None
) -> tuple[int, dict[str, object]]:
    """Return an HTTP status and JSON payload for GET/POST /api/chat."""
    method = str(environ.get("REQUEST_METHOD", "GET"))
    if method == "GET":
        return 200, _availability(context)
    if method != "POST":
        return 405, {"error": "GET or POST only"}
    if context is None:
        return 200, _availability(None)
    stream = environ.get("wsgi.input")
    if stream is None:
        return 400, {"error": "request body must be JSON"}
    try:
        length = int(str(environ.get("CONTENT_LENGTH", "0")) or "0")
        payload = json.loads(stream.read(length) or b"{}")
    except (AttributeError, json.JSONDecodeError, ValueError):
        return 400, {"error": "request body must be JSON"}
    if not isinstance(payload, dict):
        return 400, {"error": "request body must be an object"}
    message = payload.get("message")
    run_id = payload.get("run_id")
    confirmed = payload.get("confirmed", False)
    if not isinstance(message, str) or not message.strip():
        return 400, {"error": "message is required"}
    if not isinstance(run_id, str) or not run_id.strip():
        return 400, {"error": "run_id is required"}
    if not isinstance(confirmed, bool):
        return 400, {"error": "confirmed must be true or false"}
    result = _dispatch(context, message.strip(), run_id.strip(), confirmed)
    return 200, {"connected": True, "turn": _turn(result, run_id)}


def _availability(context: SurfaceContext | None) -> dict[str, object]:
    if context is None:
        return {"connected": False, "message": _NOT_CONNECTED}
    return {"connected": True}


def _dispatch(
    context: SurfaceContext, message: str, run_id: str, confirmed: bool
) -> dict[str, object]:
    tool = _QUICK_TOOLS.get(message.lower(), "command")
    request_id = uuid4().hex
    if tool == "explain":
        return dispatch_tool(
            context,
            tool,
            {"subject": message, "run_id": run_id, "request_id": request_id},
        )
    if tool in ("status", "incidents"):
        result = dispatch_tool(context, tool, {"run_id": run_id})
        return _quick_result(tool, result)
    return dispatch_tool(
        context,
        "command",
        {
            "text": message,
            "run_id": run_id,
            "confirmed": confirmed,
            "actor": "operator",
            "channel": "dashboard",
            "request_id": request_id,
        },
    )


def _quick_result(tool: str, result: dict[str, object]) -> dict[str, object]:
    if "error" in result:
        return {"outcome": "refused", "message": str(result["error"])}
    if tool == "status":
        text = str(result.get("summary", "System status is unavailable."))
    else:
        rows = result.get("incidents", [])
        if not isinstance(rows, list) or not rows:
            text = "No open incidents."
        else:
            text = "\n".join(
                f"{row.get('severity', 'unknown')}: {row.get('message', '')}"
                for row in rows
                if isinstance(row, dict)
            )
    return {"accepted": True, "outcome": "answer", "message": text}


def _turn(result: dict[str, object], run_id: str) -> dict[str, object]:
    if "error" in result:
        outcome = "refused"
        message = str(result["error"])
    else:
        outcome = str(result.get("outcome", "refused"))
        message = str(result.get("message") or result.get("reason") or "No response.")
    return {
        "role": "operator",
        "outcome": outcome,
        "message": message,
        "typed_intent": result.get("typed_intent"),
        "audit_id": result.get("audit_id"),
        "run_id": run_id,
    }
