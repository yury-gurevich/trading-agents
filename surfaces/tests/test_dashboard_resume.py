"""Dashboard resume-control end-to-end test.

Agent: surfaces
Role: prove chat intent echo, broker consequence, audit, and bounded placement.
External I/O: none; the dashboard, graph, and LLM are in-memory fakes.
"""

from __future__ import annotations

from surfaces.tests.test_dashboard_chat import _chat_app, _post


def test_resume_round_trip_echoes_consequence_and_places_audited_child() -> None:
    app, graph, _ = _chat_app()

    gate_response = _post(app, "Resume from provider")
    gated = gate_response["turn"]
    confirmed = _post(
        app,
        "Resume from provider",
        confirmed=True,
        request_id=gate_response["request_id"],
    )["turn"]

    assert gated["outcome"] == "needs_confirmation"
    assert gated["typed_intent"]["parameters"] == {
        "from_stage": "provider",
        "run_id": "chat-run",
    }
    assert (
        "re-running from portfolio manager will submit new orders at the broker"
        in gated["message"]
    )
    assert confirmed["outcome"] == "confirmed_dispatch"
    assert confirmed["message"] == "Command routed to orchestration.resume_run."
    assert (
        graph.get_node("RunRequest", "run-request:chat-run-resume-provider") is not None
    )
    assert len(graph.list_nodes("CommandAudit")) == 1
    assert len(graph.list_nodes("FlagResolution")) == 1
