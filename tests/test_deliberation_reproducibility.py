"""Reproducibility measurement tests.

Agent: tooling
Role: prove the measurement counts what it compared and never guesses the rest.
      Cites DLIB-IDM-02: the clause bounds outputs by prompt hashes, and this is
      the first thing to measure that bound. DLIB-OBS-01 is left to
      test_deliberation_replay.py, which tests reconstruction rather than counting.
External I/O: none.
"""

from __future__ import annotations

from scripts.deliberation_reproducibility import (
    measure_reproducibility,
    render_report,
)
from tests.veto_context_fixtures import intent, linked_graph, order_set

from kernel import InMemoryGraphStore
from kernel.llm_ledger import digest_text
from orchestration.deliberation_replay import replayed_user_prompt


def test_a_faithfully_recorded_turn_is_reported_as_reproducible() -> None:
    """DLIB-IDM-02: a stored hash the graph can rebuild counts as matched."""
    graph, node, orders, item = _corpus()
    _record(graph, node.key, item.ticker, _live_digest(graph, node, orders, item))

    report = measure_reproducibility(graph)

    assert report.outcomes["matched"] == 1
    assert report.compared == 1
    assert "reproducible_pct\t100.00\t(of 1 compared)" in render_report(report)


def test_a_hash_the_graph_cannot_rebuild_is_a_mismatch_not_a_pass() -> None:
    """DLIB-IDM-02: drift is counted, never rounded away."""
    graph, node, _orders, item = _corpus()
    _record(graph, node.key, item.ticker, digest_text("recorded by older code"))

    report = measure_reproducibility(graph)

    assert report.outcomes["mismatched"] == 1
    assert report.outcomes["matched"] == 0
    assert "reproducible_pct\t0.00\t(of 1 compared)" in render_report(report)


def test_an_order_that_was_never_debated_is_excluded_from_the_denominator() -> None:
    """DLIB-IDM-02: no recorded turn is not a failure to reproduce."""
    graph, _node, _orders, _item = _corpus()

    report = measure_reproducibility(graph)

    assert report.outcomes["no_recorded_turn"] == 1
    assert report.compared == 0
    assert report.orders == 1
    assert "reproducible_pct\tn/a\t(nothing was compared)" in render_report(report)


def test_a_pm_run_with_an_unreadable_order_set_is_counted_and_skipped() -> None:
    """DLIB-IDM-02: an unreadable run is named, never silently dropped."""
    graph = InMemoryGraphStore()
    graph.merge_node("PMRun", "pm-run-broken", {"order_intent_set": {"nope": 1}})
    graph.merge_node("PMRun", "pm-run-empty", {})

    report = measure_reproducibility(graph)

    assert report.pm_runs == 2
    assert report.unreadable_runs == 2
    assert report.orders == 0


def test_run_ids_narrow_the_corpus_without_changing_the_measurement() -> None:
    """DLIB-IDM-02: the filter selects runs; it does not reinterpret them."""
    graph, node, orders, item = _corpus()
    _record(graph, node.key, item.ticker, _live_digest(graph, node, orders, item))
    graph.merge_node("PMRun", "pm-run-other", {"order_intent_set": {"nope": 1}})

    everything = measure_reproducibility(graph)
    narrowed = measure_reproducibility(graph, run_ids=(node.key,))

    assert everything.pm_runs == 2
    assert narrowed.pm_runs == 1
    assert narrowed.unreadable_runs == 0
    assert narrowed.outcomes["matched"] == 1


def test_a_call_without_a_correlation_id_or_hash_is_not_indexed() -> None:
    """DLIB-IDM-02: a malformed ledger row cannot masquerade as evidence."""
    graph, node, _orders, item = _corpus()
    graph.merge_node("LLMCall", "call-no-corr", {"prompt_hash": "deadbeef"})
    graph.merge_node(
        "LLMCall", "call-no-hash", {"correlation_id": f"{node.key}:{item.ticker}:x:r1"}
    )

    report = measure_reproducibility(graph)

    assert report.outcomes["no_recorded_turn"] == 1
    assert report.compared == 0


def _corpus() -> tuple[InMemoryGraphStore, object, object, object]:
    graph = InMemoryGraphStore()
    item = intent()
    orders = order_set(item)
    node = linked_graph(graph, full=True)
    node = graph.merge_node(
        "PMRun", node.key, {"order_intent_set": orders.model_dump(mode="json")}
    )
    return graph, node, orders, item


def _live_digest(graph: object, node: object, orders: object, item: object) -> str:
    return digest_text(replayed_user_prompt(graph, node, orders, item))  # type: ignore[arg-type]


def _record(graph: InMemoryGraphStore, pm_key: str, ticker: str, digest: str) -> None:
    graph.merge_node(
        "LLMCall",
        f"call-{ticker}",
        {
            "correlation_id": f"{pm_key}:{ticker}:defender:r1",
            "prompt_hash": digest,
        },
    )
