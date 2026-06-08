"""Analyst graph-store tests.

Agent: analyst
Role: verify recommendation graph writes tolerate missing candidate lineage.
External I/O: none.
"""

from __future__ import annotations

from agents.analyst.store import write_analysis
from agents.analyst.tests.helpers import candidate, candidate_set, recommendation
from contracts.common import Provenance
from kernel import InMemoryGraphStore


def test_write_analysis_skips_invalid_scan_graph_id() -> None:
    graph = InMemoryGraphStore()
    scan = candidate_set(candidate())
    scan = scan.model_copy(
        update={"provenance": Provenance(run_id="x", source_agent="scanner")}
    )

    provenance = write_analysis(
        graph,
        candidate_set=scan,
        recommendations=(recommendation(),),
        rejections=(),
    )

    rec = graph.get_node("Recommendation", f"{provenance.run_id}:AAPL")
    assert rec is not None
    assert list(graph.descendants(rec, max_depth=1)) == []


def test_write_analysis_skips_missing_candidate_node() -> None:
    graph = InMemoryGraphStore()

    provenance = write_analysis(
        graph,
        candidate_set=candidate_set(candidate()),
        recommendations=(recommendation(),),
        rejections=(),
    )

    rec = graph.get_node("Recommendation", f"{provenance.run_id}:AAPL")
    assert rec is not None
    assert list(graph.descendants(rec, max_depth=1)) == []
