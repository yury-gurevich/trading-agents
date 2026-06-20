"""P7 boundary test proving researcher never applies proposals.

Agent: researcher
Role: prove proposed and approved changes do not mutate analyst settings.
External I/O: none.
"""

from __future__ import annotations

from agents.researcher.settings import ResearcherSettings
from agents.researcher.tests.helpers import bound_bus, propose, seed_snapshots
from kernel import InMemoryGraphStore


def test_researcher_never_applies_proposed_change() -> None:
    """RES-NEV-01: researcher proposes, never applies; settings unchanged."""
    graph = InMemoryGraphStore()
    bus = bound_bus(graph)
    seed_snapshots(graph, confidence=0.35)
    original = ResearcherSettings().confidence_floor_reference

    proposal = propose(bus)
    _resolve(graph, proposal.proposal_id)

    assert graph.list_nodes("Experiment")
    assert graph.list_nodes("FlagResolution")
    assert ResearcherSettings().confidence_floor_reference == original


def _resolve(graph: InMemoryGraphStore, proposal_id: str) -> None:
    graph.merge_node(
        "FlagResolution",
        f"resolution:flag:proposal:{proposal_id}:info",
        {"subject_ref": f"proposal:{proposal_id}", "severity": "info"},
    )
