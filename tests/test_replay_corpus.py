"""Corpus rebuild tests.

Agent: tooling
Role: prove the replay corpus is rebuilt from stored state and states its own
      denominator.
External I/O: none.
"""

from __future__ import annotations

from tests.veto_context_fixtures import intent, linked_graph, order_set

from kernel import InMemoryGraphStore
from orchestration.replay_corpus import build_corpus
from orchestration.veto_context import build_veto_context


def test_every_approved_order_becomes_one_replayable_subject() -> None:
    """The unit of debate is an order, not a run."""
    graph, node, orders, item = _corpus()

    corpus = build_corpus(graph)

    assert corpus.pm_runs == 1
    assert [subject.ticker for subject in corpus.subjects] == [item.ticker]
    assert corpus.subjects[0].pm_run == node.key
    assert corpus.subjects[0].proposition.context == build_veto_context(
        graph, node, orders, item
    )


def test_the_decision_line_matches_the_one_the_live_manager_builds() -> None:
    """A different decision line is a different prompt, so a different measure."""
    graph, _node, _orders, item = _corpus()

    assert build_corpus(graph).subjects[0].proposition.decision == (
        f"{item.action} {item.ticker} (qty {item.quantity})"
    )


def test_a_run_with_no_readable_order_set_is_counted_not_dropped() -> None:
    """Early-return runs are a real category; silence about them is a defect."""
    graph = InMemoryGraphStore()
    graph.merge_node("PMRun", "pm-run-empty", {})
    graph.merge_node("PMRun", "pm-run-broken", {"order_intent_set": {"nope": 1}})

    corpus = build_corpus(graph)

    assert (corpus.pm_runs, corpus.unreadable_runs) == (2, 2)
    assert corpus.subjects == ()
    assert corpus.detail() == "pm_runs=2; unreadable_runs=2; subjects=0"


def test_run_ids_narrow_the_corpus_without_reinterpreting_it() -> None:
    """Choosing the sample is the point of replay; it must not change the reads."""
    graph, node, _orders, _item = _corpus()
    graph.merge_node("PMRun", "pm-run-other", {"order_intent_set": {"nope": 1}})

    narrowed = build_corpus(graph, run_ids=(node.key,))

    assert build_corpus(graph).pm_runs == 2
    assert (narrowed.pm_runs, narrowed.unreadable_runs) == (1, 0)
    assert len(narrowed.subjects) == 1


def _corpus() -> tuple[InMemoryGraphStore, object, object, object]:
    graph = InMemoryGraphStore()
    item = intent()
    orders = order_set(item)
    node = linked_graph(graph, full=True)
    node = graph.merge_node(
        "PMRun", node.key, {"order_intent_set": orders.model_dump(mode="json")}
    )
    return graph, node, orders, item
