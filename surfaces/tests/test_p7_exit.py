"""P7 exit tests for researcher proposal review.

Agent: surfaces
Role: prove proposals can be created, approved, inspected, and never applied.
External I/O: none.
"""

from __future__ import annotations

from agents.analyst.settings import AnalystSettings
from contracts.common import Explanation, Provenance
from contracts.operator import TypedIntent
from contracts.researcher import ParameterChangeProposal, ResearchRequest
from contracts.supervisor import DispatchResult
from kernel import AgentMessage, InMemoryGraphStore
from surfaces.context import SurfaceContext
from surfaces.context import test_context as build_context
from surfaces.queries import all_proposals


def test_p7_propose_creates_experiment_param_change_and_flag() -> None:
    graph = InMemoryGraphStore()
    ctx = _ctx_with_snapshots(graph, confidence=0.35)

    proposal = _propose(ctx)

    assert proposal.changes
    assert graph.list_nodes("Experiment")
    assert graph.list_nodes("ParamChange")
    assert graph.list_nodes("Flag")


def test_p7_approve_proposal_marks_surface_view_approved() -> None:
    graph = InMemoryGraphStore()
    ctx = _ctx_with_snapshots(graph, confidence=0.35)
    proposal = _propose(ctx)

    result = _approve(ctx, proposal.proposal_id)

    assert result.accepted
    assert all_proposals(graph)[0].approved


def test_p7_never_applies_after_approval() -> None:
    graph = InMemoryGraphStore()
    ctx = _ctx_with_snapshots(graph, confidence=0.35)
    original = AnalystSettings().confidence_floor
    proposal = _propose(ctx)

    _approve(ctx, proposal.proposal_id)

    assert AnalystSettings().confidence_floor == original


def test_p7_evidence_query_returns_explanation() -> None:
    graph = InMemoryGraphStore()
    ctx = _ctx_with_snapshots(graph, confidence=0.35)

    response = ctx.bus.request(
        AgentMessage(
            sender="test",
            recipient="researcher",
            message_type="request",
            capability="evidence",
            payload=ResearchRequest().model_dump(mode="json"),
        )
    )
    explanation = Explanation.model_validate(response.payload)

    assert explanation.summary


def _ctx_with_snapshots(
    graph: InMemoryGraphStore, *, confidence: float
) -> SurfaceContext:
    ctx = build_context(graph=graph)
    _seed_snapshots(graph, confidence=confidence)
    return ctx


def _approve(ctx: SurfaceContext, proposal_id: str) -> DispatchResult:
    response = ctx.bus.request(
        AgentMessage(
            sender="test",
            recipient="supervisor",
            message_type="request",
            capability="dispatch_intent",
            payload=_approve_payload(proposal_id),
        )
    )
    return DispatchResult.model_validate(response.payload)


def _propose(ctx: SurfaceContext) -> ParameterChangeProposal:
    response = ctx.bus.request(
        AgentMessage(
            sender="test",
            recipient="researcher",
            message_type="request",
            capability="propose",
            payload=ResearchRequest().model_dump(mode="json"),
        )
    )
    return ParameterChangeProposal.model_validate(response.payload)


def _approve_payload(proposal_id: str) -> dict[str, object]:
    return TypedIntent(
        family="approve",
        parameters={"confirmed": "true", "subject": f"proposal:{proposal_id}"},
        requires_confirmation=True,
        provenance=Provenance(run_id="p7-approve", source_agent="operator"),
    ).model_dump(mode="json")


def _seed_snapshots(graph: InMemoryGraphStore, *, confidence: float) -> None:
    for index in range(6):
        graph.merge_node(
            "Snapshot",
            f"snapshot:run-{index}",
            {
                "run_id": f"run-{index}",
                "metrics": {
                    "portfolio": {"approval_rate": 0.80},
                    "signal": {
                        "avg_confidence": confidence,
                        "rejection_count": 1.0,
                    },
                },
            },
        )
