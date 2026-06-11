"""Proposal surface tests.

Agent: surfaces
Role: verify proposal query projections and CLI rendering.
External I/O: none.
"""

from __future__ import annotations

from io import StringIO

from kernel import InMemoryGraphStore
from surfaces.cli import main
from surfaces.context import test_context as build_context
from surfaces.queries import all_proposals
from surfaces.render_review import render_proposals


def test_all_proposals_projects_pending_and_approved_status() -> None:
    graph = InMemoryGraphStore()
    assert all_proposals(graph) == ()
    _proposal(graph, "pending", "2026-06-11T00:00:00+00:00")
    _proposal(graph, "approved", "2026-06-12T00:00:00+00:00")
    graph.merge_node(
        "FlagResolution",
        "resolution:flag:proposal:approved:info",
        {"subject_ref": "proposal:approved", "severity": "info"},
    )

    proposals = all_proposals(graph)

    assert [proposal.proposal_id for proposal in proposals] == ["approved", "pending"]
    assert proposals[0].approved is True
    assert proposals[1].approved is False
    assert "approved" in render_proposals(proposals)


def test_cli_proposals_renders_empty_and_pending_proposal() -> None:
    graph = InMemoryGraphStore()
    empty = StringIO()
    pending = StringIO()

    main(["proposals"], context=build_context(graph=graph), stdout=empty)
    _proposal(graph, "p1", "2026-06-11T00:00:00+00:00")
    main(["proposals"], context=build_context(graph=graph), stdout=pending)

    assert "no proposals pending review" in empty.getvalue()
    assert "p1" in pending.getvalue()
    assert "pending" in pending.getvalue()


def _proposal(graph: InMemoryGraphStore, proposal_id: str, created_at: str) -> None:
    graph.merge_node(
        "Experiment",
        f"experiment:{proposal_id}",
        {
            "proposal_id": proposal_id,
            "change_count": 1,
            "rationale_summary": "bounded change",
            "created_at": created_at,
        },
    )
