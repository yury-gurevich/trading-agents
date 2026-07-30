"""Graph vocabulary and guarded-store tests.

Agent: kernel
Role: cover the declared-vocabulary checks and the write-time guard.
External I/O: none.
"""

from __future__ import annotations

import pytest

from kernel import InMemoryGraphStore
from kernel.graph_guarded import GuardedGraphStore
from kernel.graph_vocabulary import Vocabulary, VocabularyError

_DECLARATION = {
    "labels": ["Run", "Item"],
    "edge_types": ["MADE"],
    "edge_signatures": [["Item", "MADE", "Run"]],
    "owners": {"scanner": ["Item"]},
    "properties": {"Item": ["status"]},
}


def _vocab(**overrides: object) -> Vocabulary:
    return Vocabulary.from_mapping({**_DECLARATION, **overrides})


def _guarded(**overrides: object) -> tuple[InMemoryGraphStore, GuardedGraphStore]:
    inner = InMemoryGraphStore()
    writer = str(overrides.pop("writer", ""))
    return inner, GuardedGraphStore(inner, _vocab(**overrides), writer=writer)


def test_empty_declaration_yields_an_empty_vocabulary() -> None:
    vocabulary = Vocabulary.from_mapping({})
    assert vocabulary.labels == frozenset()
    assert vocabulary.edge_types == frozenset()
    assert vocabulary.edge_signatures == frozenset()
    assert dict(vocabulary.owners) == {}
    assert dict(vocabulary.properties) == {}


def test_malformed_signature_rows_are_ignored_not_half_parsed() -> None:
    """A row that is not a triple is skipped — never a partial signature."""
    vocabulary = Vocabulary.from_mapping(
        {"edge_signatures": [["Item", "MADE"], ["Item", "MADE", "Run"], "junk"]}
    )
    assert vocabulary.edge_signatures == frozenset({("Item", "MADE", "Run")})


def test_declared_label_passes() -> None:
    _vocab().check_node("Run")


def test_declared_property_passes() -> None:
    _vocab().check_node("Item", props={"status": "new"})


def test_undeclared_property_is_rejected() -> None:
    with pytest.raises(VocabularyError, match="undeclared properties"):
        _vocab().check_node("Item", props={"typo_status": "new"})


def test_label_without_property_declaration_is_unconstrained() -> None:
    _vocab().check_node("Run", props={"freeform": "ok"})


def test_undeclared_label_is_rejected() -> None:
    with pytest.raises(VocabularyError, match="undeclared node label 'Postion'"):
        _vocab().check_node("Postion")


def test_writer_may_not_write_outside_its_declared_labels() -> None:
    with pytest.raises(VocabularyError, match="may not write label 'Run'"):
        _vocab().check_node("Run", writer="scanner")


def test_writer_with_no_declaration_is_unconstrained() -> None:
    """Ownership only binds writers that declared something."""
    _vocab().check_node("Run", writer="analyst")


def test_declared_edge_signature_passes() -> None:
    _vocab().check_edge("Item", "MADE", "Run")


def test_undeclared_edge_type_is_rejected() -> None:
    with pytest.raises(VocabularyError, match="undeclared edge type 'MAED'"):
        _vocab().check_edge("Item", "MAED", "Run")


def test_undeclared_edge_shape_is_rejected() -> None:
    with pytest.raises(VocabularyError, match="not declared to run Run -> Item"):
        _vocab().check_edge("Run", "MADE", "Item")


def test_no_declared_signatures_means_shape_is_unchecked() -> None:
    _vocab(edge_signatures=[]).check_edge("Run", "MADE", "Item")


def test_guard_delegates_a_conforming_write() -> None:
    inner, graph = _guarded()
    item = graph.merge_node("Item", "a", {})
    run = graph.merge_node("Run", "r", {})
    graph.add_edge(item, run, "MADE")
    assert inner.get_node("Item", "a") is not None
    assert [n.key for n in inner.list_nodes("Run")] == ["r"]


def test_guard_blocks_the_write_before_it_reaches_the_store() -> None:
    inner, graph = _guarded()
    with pytest.raises(VocabularyError):
        graph.merge_node("Postion", "a", {})
    assert inner.list_nodes("Postion") == ()


def test_guard_blocks_a_bad_edge_before_it_reaches_the_store() -> None:
    inner, graph = _guarded()
    item = graph.merge_node("Item", "a", {})
    run = graph.merge_node("Run", "r", {})
    with pytest.raises(VocabularyError):
        graph.add_edge(run, item, "MADE")
    assert list(inner.ancestors(run, max_depth=2)) == []


def test_guard_passes_reads_straight_through() -> None:
    _, graph = _guarded()
    item = graph.merge_node("Item", "a", {})
    run = graph.merge_node("Run", "r", {})
    graph.add_edge(item, run, "MADE")
    assert graph.get_node("Item", "a") == item
    assert graph.list_nodes("Run") == (run,)
    assert [n.key for n in graph.ancestors(run, max_depth=2)] == ["a"]
    assert [n.key for n in graph.descendants(item, max_depth=2)] == ["r"]
