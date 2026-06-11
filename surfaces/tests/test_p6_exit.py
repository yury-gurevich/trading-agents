"""P6 exit criterion test.

Agent: surfaces
Role: prove run, inspect, approve, recover, and explain are operator-reachable.
External I/O: none.
"""

from __future__ import annotations

from contracts.common import Provenance
from contracts.operator import CommandResult, HumanCommand, TypedIntent
from contracts.reporter import NarrativeRequest, TradeNarrative
from contracts.supervisor import DispatchResult, MasterReport
from kernel import AgentMessage, FakeLLMClient, InMemoryGraphStore
from surfaces.context import SurfaceContext
from surfaces.context import test_context as build_context
from surfaces.queries import open_faults


def test_p6_operator_checklist_run_inspect_approve_recover_explain() -> None:
    graph = InMemoryGraphStore()
    ctx = build_context(graph=graph, llm=_run_llm())

    parsed = CommandResult.model_validate(
        _request(
            ctx,
            "operator",
            "interpret",
            HumanCommand(
                text="run the daily scan",
                actor="test",
                channel="dashboard",
            ).model_dump(mode="json"),
        ).payload
    )
    if parsed.intent is None:
        raise AssertionError("operator did not return an intent")
    routed = DispatchResult.model_validate(
        _request(
            ctx, "supervisor", "dispatch_intent", parsed.intent.model_dump()
        ).payload
    )
    assert routed.accepted
    assert routed.routed_to == "orchestration.execute_run"

    status = MasterReport.model_validate(
        _request(ctx, "supervisor", "system_status", {}).payload
    )
    assert status.summary.summary

    _seed_fault(graph)
    assert any(fault.source_agent == "analyst" for fault in open_faults(graph))

    graph.merge_node(
        "Flag",
        "flag:run/test-123:critical",
        {"subject_ref": "run/test-123", "severity": "critical"},
    )
    approved = DispatchResult.model_validate(
        _request(ctx, "supervisor", "dispatch_intent", _approve_payload()).payload
    )
    assert approved.accepted
    assert graph.list_nodes("FlagResolution")

    graph.merge_node("Position", "run-a:AAPL", {"run_id": "run-a", "ticker": "AAPL"})
    narrative = TradeNarrative.model_validate(
        _request(
            ctx,
            "reporter",
            "narrative",
            NarrativeRequest(position_id="run-a:AAPL").model_dump(),
        ).payload
    )
    assert narrative.story.summary


def _request(
    ctx: SurfaceContext, recipient: str, capability: str, payload: dict[str, object]
) -> AgentMessage:
    return ctx.bus.request(
        AgentMessage(
            sender="test",
            recipient=recipient,
            message_type="request",
            capability=capability,
            payload=payload,
        )
    )


def _approve_payload() -> dict[str, object]:
    return TypedIntent(
        family="approve",
        parameters={"confirmed": "true", "subject": "run/test-123"},
        requires_confirmation=True,
        provenance=Provenance(run_id="p6-approve", source_agent="operator"),
    ).model_dump(mode="json")


def _seed_fault(graph: InMemoryGraphStore) -> None:
    graph.merge_node(
        "Fault",
        "fault:analyst:p6",
        {
            "source_agent": "analyst",
            "capability": "analyze",
            "severity": "critical",
            "message": "analysis failed",
            "occurred_at": "2026-06-11T00:00:00+00:00",
        },
    )


def _run_llm() -> FakeLLMClient:
    return FakeLLMClient(
        {"run": '{"outcome":"intent","family":"run","parameters":{"confirmed":"true"}}'}
    )
