"""Dashboard operator-chat endpoint and audit-ledger tests.

Agent: surfaces
Role: prove every chat outcome, run grounding, explicit confirmation, and isolation.
External I/O: none; graph, LLM, and WSGI requests are in-memory fakes.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, cast

from kernel import InMemoryGraphStore
from orchestration.start import place_run_request
from surfaces.context import build_test_context
from surfaces.dashboard import build_app, chat_binding
from surfaces.tests.test_dashboard_app import invoke

if TYPE_CHECKING:
    import pytest


class _ChatLLM:
    def __init__(self) -> None:
        self.explain_user = ""
        self.interpret_user = ""

    def complete(
        self, *, system: str, user: str, tool_schema: dict[str, object]
    ) -> str:
        del system
        if not tool_schema:
            self.explain_user = user
            return "The selected run completed with evidence from its stored stages."
        self.interpret_user = user
        if "unsafe" in user:
            return (
                '{"outcome":"refused","reason":'
                '"That request is outside the bounded controls."}'
            )
        if "ambiguous" in user:
            return (
                '{"outcome":"needs_clarification","reason":"Which action do you mean?"}'
            )
        if "start scan" in user:
            return '{"outcome":"intent","family":"run","parameters":{"stage":"paper"}}'
        if "resume from provider" in user.lower():
            return (
                '{"outcome":"intent","family":"resume",'
                '"parameters":{"from_stage":"provider"}}'
            )
        return (
            '{"outcome":"intent","family":"explain",'
            '"parameters":{"subject":"how the selected run performed"}}'
        )


def _post(
    app: Any, message: str, *, confirmed: bool = False, request_id: str | None = None
) -> dict[str, Any]:
    payload = json.dumps(
        {
            "message": message,
            "run_id": "chat-run",
            "confirmed": confirmed,
            "request_id": request_id,
        }
    ).encode()
    status, _, body = invoke(app, "/api/chat", "POST", payload)
    assert status == "200 OK"
    return cast("dict[str, Any]", json.loads(body))


def _chat_app() -> tuple[Any, InMemoryGraphStore, _ChatLLM]:
    graph = InMemoryGraphStore()
    place_run_request(graph, run_id="chat-run", tickers=("AAPL",))
    llm = _ChatLLM()
    context = build_test_context(graph=graph, llm=llm)
    return build_app(graph, chat_context=context), graph, llm


def test_chat_full_outcome_table_and_explicit_confirmation() -> None:
    app, _, _ = _chat_app()
    assert json.loads(invoke(app, "/api/chat")[2]) == {"connected": True}

    answer = _post(app, "how did we go last night")["turn"]
    refused = _post(app, "unsafe request")["turn"]
    clarify = _post(app, "ambiguous request")["turn"]
    gated = _post(app, "start scan")["turn"]
    confirmed = _post(app, "start scan", confirmed=True)["turn"]

    assert answer["outcome"] == "answer"
    assert answer["run_id"] == "chat-run"
    assert refused["outcome"] == "refused"
    assert clarify["outcome"] == "needs_clarification"
    assert gated["outcome"] == "needs_confirmation"
    assert gated["typed_intent"] == {
        "family": "run",
        "parameters": {"stage": "paper"},
        "requires_confirmation": True,
    }
    assert confirmed["outcome"] == "confirmed_dispatch"
    assert confirmed["message"] == "Command routed to orchestration.execute_run."


def test_chat_answer_is_run_grounded_and_writes_priced_ledger_nodes() -> None:
    app, graph, llm = _chat_app()
    turn = _post(app, "how did we go last night")["turn"]

    assert "Selected run: chat-run" in llm.explain_user
    assert "Selected run: chat-run" in llm.interpret_user
    assert '"key": "run-request:chat-run"' in llm.explain_user
    assert '"label": "RunRequest"' in llm.explain_user
    assert turn["audit_id"].startswith("audit:")
    assert len(graph.list_nodes("CommandAudit")) == 2
    assert len(graph.list_nodes("LLMCall")) == 2
    assert len(graph.list_nodes("Intent")) == 1


def test_repeated_chat_message_appends_a_fresh_priced_exchange() -> None:
    app, graph, _ = _chat_app()

    first = _post(app, "how did we go last night")["turn"]
    second = _post(app, "how did we go last night")["turn"]

    assert first["audit_id"] != second["audit_id"]
    assert len(graph.list_nodes("CommandAudit")) == 4
    assert len(graph.list_nodes("LLMCall")) == 4
    assert len(graph.list_nodes("Intent")) == 2


def test_chat_suggested_asks_use_existing_bounded_tools() -> None:
    app, _, _ = _chat_app()
    explained = _post(app, "Explain this run")["turn"]
    status = _post(app, "System status")["turn"]
    incidents = _post(app, "Open incidents")["turn"]

    assert explained["outcome"] == "answer"
    assert status["outcome"] == "answer"
    assert incidents["message"] == "No open incidents."


def test_chat_unbound_invalid_requests_and_method_guard() -> None:
    app = build_app(InMemoryGraphStore())
    unavailable = json.loads(invoke(app, "/api/chat")[2])
    post_unavailable = json.loads(
        invoke(app, "/api/chat", "POST", b'{"message":"hi"}')[2]
    )
    assert (
        unavailable
        == post_unavailable
        == {
            "connected": False,
            "message": "chat is not connected on this deployment",
        }
    )
    connected, _, _ = _chat_app()
    for body in (b"nope", b"[]", b"{}", b'{"message":"hi","run_id":"r","confirmed":1}'):
        assert invoke(connected, "/api/chat", "POST", body)[0] == "400 Bad Request"
    assert invoke(connected, "/api/chat", "DELETE")[0] == "405 Method Not Allowed"


def test_chat_binding_requires_live_graph_and_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    graph = InMemoryGraphStore()
    assert chat_binding.bind_dashboard_chat(graph, {}) is None
    assert (
        chat_binding.bind_dashboard_chat(
            graph,
            {"ANTHROPIC_API_KEY": "test-key"},  # pragma: allowlist secret
        )
        is None
    )
    assert (
        chat_binding.bind_dashboard_chat(
            None,
            {
                "ANTHROPIC_API_KEY": "test-key",  # pragma: allowlist secret
                "POSTGRES_DSN": "bound",
            },
        )
        is None
    )
    monkeypatch.setattr(
        chat_binding, "AnthropicLLMClient", lambda **_kwargs: _ChatLLM()
    )
    bound = chat_binding.bind_dashboard_chat(
        graph,
        {
            "ANTHROPIC_API_KEY": "test-key",  # pragma: allowlist secret
            "POSTGRES_DSN": "bound",
        },
    )
    assert bound is not None
    assert bound.graph is graph
