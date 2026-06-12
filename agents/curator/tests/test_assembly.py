"""Curator assembly tests.

Agent: curator
Role: verify provenance traversal yields ordered, labelled example records.
External I/O: none.
"""

from __future__ import annotations

from agents.curator.domain.assembly import assemble_examples
from agents.curator.tests.helpers import seed_narratives
from kernel import InMemoryGraphStore


def test_empty_graph_yields_no_records() -> None:
    graph = InMemoryGraphStore()
    assert assemble_examples(graph, purpose="exit-timing", max_examples=10) == ()


def test_five_narratives_yield_labelled_ordered_records() -> None:
    graph = InMemoryGraphStore()
    seed_narratives(graph, 5, trigger="target")

    records = assemble_examples(graph, purpose="exit-timing", max_examples=10)

    assert len(records) == 5
    assert all(record.label == "target" for record in records)
    assert [record.example_id for record in records] == sorted(
        record.example_id for record in records
    )
    assert records[0].content == "story 0"
    assert records[0].metadata["ticker"] == "TICK0"


def test_narrative_without_close_decision_is_unlabelled() -> None:
    graph = InMemoryGraphStore()
    seed_narratives(graph, 1, trigger=None)

    records = assemble_examples(graph, purpose="exit-timing", max_examples=10)

    assert records[0].label == "unlabelled"


def test_narrative_without_position_is_unlabelled_without_ticker() -> None:
    graph = InMemoryGraphStore()
    graph.merge_node(
        "TradeNarrative",
        "narrative:orphan",
        {"run_id": "run-x", "position_id": "orphan", "summary": "lonely"},
    )

    records = assemble_examples(graph, purpose="exit-timing", max_examples=10)

    assert records[0].label == "unlabelled"
    assert "ticker" not in records[0].metadata


def test_max_examples_truncates_in_key_order() -> None:
    graph = InMemoryGraphStore()
    seed_narratives(graph, 5, trigger="stop")

    records = assemble_examples(graph, purpose="exit-timing", max_examples=2)

    assert len(records) == 2
    assert records[0].content == "story 0"
    assert records[1].content == "story 1"
