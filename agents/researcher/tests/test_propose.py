"""Researcher agent proposal tests.

Agent: researcher
Role: verify bus capability writes proposal graph artifacts and review flags.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from agents.researcher import ResearcherAgent
from agents.researcher.tests.helpers import (
    bound_bus,
    evidence_summary,
    propose,
    request,
    seed_snapshots,
)
from contracts.researcher import ParameterChangeProposal
from kernel import CollectingFaultSink, InMemoryGraphStore, InProcessBus

if TYPE_CHECKING:
    from kernel import GraphStore


def test_propose_writes_graph_nodes_and_flag() -> None:
    """RES-IN-01 / RES-TRG-01 / RES-OUT-01 / RES-OUT-02 / RES-OUT-04:
    propose → proposal + nodes + Flag."""
    graph = InMemoryGraphStore()
    bus = bound_bus(graph)
    seed_snapshots(graph, confidence=0.35)

    proposal = propose(bus)

    assert proposal.changes
    assert len(graph.list_nodes("Experiment")) == 1
    assert len(graph.list_nodes("ParamChange")) == 1
    assert any(
        str(flag.props.get("subject_ref", "")).startswith("proposal:")
        for flag in graph.list_nodes("Flag")
    )


def test_propose_insufficient_evidence_writes_no_flag() -> None:
    """RES-NEV-02 / RES-OUT-05: insufficient data → zero changes; no Flag."""
    graph = InMemoryGraphStore()
    proposal = propose(bound_bus(graph))

    assert not proposal.changes
    assert graph.list_nodes("Flag") == ()


def test_propose_neutral_evidence_writes_experiment_without_flag() -> None:
    """RES-OUT-04 / RES-OUT-05: neutral evidence → Experiment; no Flag."""
    graph = InMemoryGraphStore()
    bus = bound_bus(graph)
    seed_snapshots(graph, confidence=0.50)

    proposal = propose(bus)

    assert not proposal.changes
    assert len(graph.list_nodes("Experiment")) == 1
    assert graph.list_nodes("ParamChange") == ()
    assert graph.list_nodes("Flag") == ()


def test_evidence_capability_reports_metrics_and_insufficient_data() -> None:
    """RES-IN-02 / RES-TRG-02 / RES-OUT-03 / RES-IDM-03: evidence RPC → Explanation."""
    empty_bus = bound_bus(InMemoryGraphStore())
    full_graph = InMemoryGraphStore()
    full_bus = bound_bus(full_graph)
    seed_snapshots(full_graph, confidence=0.35)

    empty = evidence_summary(empty_bus)
    full = evidence_summary(full_bus)

    assert "insufficient data" in empty
    assert "avg_confidence=0.35" in full


def test_researcher_degrades_on_graph_fault() -> None:
    """RES-FAIL-01 / RES-FAIL-02 / RES-IN-03: graph fault → zero-change proposal +
    Explanation; fault emitted."""
    bus = InProcessBus()
    sink = CollectingFaultSink()
    ResearcherAgent(bus, graph=cast("GraphStore", _BrokenGraph()), sink=sink).bind()

    proposal = ParameterChangeProposal.model_validate(request(bus, "propose").payload)
    explanation = request(bus, "evidence").payload

    assert not proposal.changes
    assert "failed" in proposal.rationale.summary
    assert "failed" in str(explanation["summary"])
    assert len(sink.faults) == 2


class _BrokenGraph:
    def list_nodes(self, label: str) -> tuple[object, ...]:
        raise RuntimeError(label)
