"""Offline dashboard chat completion fixtures.

Agent: surfaces
Role: send a chat turn through real operator adapters on scripted SDKs.
External I/O: none; in-memory graph and bus only.
"""

from __future__ import annotations

import json
from io import BytesIO
from typing import TYPE_CHECKING, cast

from agents.operator.tests.cutoff_helpers import (
    EXPLAIN_INTENT,
    PARTIAL_ANSWER,
    scripted_client,
    vendor_reply,
)
from kernel import CollectingFaultSink, InMemoryGraphStore, InProcessBus
from surfaces.context import build_test_context
from surfaces.dashboard.chat import handle_chat

if TYPE_CHECKING:
    import pytest


def chat_case(
    monkeypatch: pytest.MonkeyPatch,
    provider: str,
    phase: str,
    *,
    partial: bool = False,
    failed: bool = False,
) -> tuple[dict[str, object], InMemoryGraphStore, CollectingFaultSink]:
    """Pin settings independently of .env and expose the actual fault sink."""
    monkeypatch.setenv("OPERATOR_LLM_PROVIDER", provider)
    monkeypatch.delenv("OPERATOR_MODEL", raising=False)
    monkeypatch.delenv("OPERATOR_EFFORT", raising=False)
    stopped = "max_tokens" if provider == "anthropic" else "max_output_tokens"
    data: dict[str, object] | None = {"answer": PARTIAL_ANSWER} if partial else None
    replies = [
        TimeoutError("fixture request timed out")
        if failed
        else vendor_reply(provider, stopped, data)
    ]
    if phase == "answer":
        finished = "tool_use" if provider == "anthropic" else "completed"
        replies.insert(0, vendor_reply(provider, finished, EXPLAIN_INTENT))
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
            "run_id": "cutoff-run",
            "request_id": f"cutoff-{phase}",
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
