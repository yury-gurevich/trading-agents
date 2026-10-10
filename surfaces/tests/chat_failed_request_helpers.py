"""Failed-request chat fixtures using real adapters on fake SDKs.

Agent: surfaces
Role: exercise quick, parse, and answer failures with pinned vendor settings.
External I/O: none; SDK imports and requests are injected fakes.
"""

from __future__ import annotations

import json
from io import BytesIO
from typing import TYPE_CHECKING, cast

from agents.operator.tests.cutoff_helpers import (
    EXPLAIN_INTENT,
    scripted_client,
    vendor_reply,
)
from kernel import CollectingFaultSink, InMemoryGraphStore, InProcessBus
from surfaces.context import build_test_context
from surfaces.dashboard.chat import handle_chat

if TYPE_CHECKING:
    import pytest

STATUS_ERROR = (
    "Error code: 400 - {'type': 'error', 'error': {'type': 'invalid_request_error', "
    "'message': 'Your credit balance is too low to access the API.'}, "
    "'request_id': 'req_011'}"
)


def failed_chat_case(
    monkeypatch: pytest.MonkeyPatch, provider: str, phase: str, failure: str
) -> tuple[dict[str, object], InMemoryGraphStore, CollectingFaultSink]:
    """Send one turn with no dependency on a .env or installed vendor SDK."""
    monkeypatch.setenv("OPERATOR_LLM_PROVIDER", provider)
    monkeypatch.delenv("OPERATOR_MODEL", raising=False)
    monkeypatch.delenv("OPERATOR_EFFORT", raising=False)
    error = (
        RuntimeError(STATUS_ERROR)
        if failure == "status"
        else TimeoutError("Request timed out." if failure == "timeout" else "")
    )
    replies: list[object] = [error]
    if phase == "answer":
        stop = "completed" if provider == "openai" else "tool_use"
        replies.insert(0, vendor_reply(provider, stop, EXPLAIN_INTENT))
    client, requests = scripted_client(monkeypatch, provider, replies)
    graph = InMemoryGraphStore()
    context = build_test_context(graph=graph, llm=client)
    assert isinstance(context.bus, InProcessBus)
    assert isinstance(context.bus.sink, CollectingFaultSink)
    body = json.dumps(
        {
            "message": "explain this run"
            if phase == "quick"
            else "What happened in this run?",
            "run_id": "failed-request-run",
            "request_id": f"failed-request-{phase}",
        }
    ).encode()
    status, payload = handle_chat(
        {
            "REQUEST_METHOD": "POST",
            "CONTENT_LENGTH": str(len(body)),
            "wsgi.input": BytesIO(body),
        },
        context,
    )
    assert status == 200
    assert len(requests) == len(replies)
    return cast("dict[str, object]", payload["turn"]), graph, context.bus.sink
