"""Repeat-row reader proofs for S256.

Agent: tooling
Role: prove cost and outage readers include repeats, while replay uses originals.
External I/O: none; in-memory graph and committed pricing only.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from scripts import check_llm_outage
from scripts.deliberation_reproducibility import measure_reproducibility
from tests.veto_context_fixtures import intent, linked_graph, order_set

from kernel import InMemoryGraphStore, Node
from kernel.llm_ledger import write_llm_call
from kernel.llm_outage import outage_report
from kernel.llm_tokens import SOURCE_VENDOR
from orchestration.deliberation_replay import replayed_prompt_digest
from surfaces.dashboard.llm_costs import llm_cost_projection


def write_turn(
    graph: InMemoryGraphStore, *, corr: str, prompt: str, tokens: int
) -> Node:
    return write_llm_call(
        graph,
        calling_agent="deliberator-proponent",
        correlation_id=corr,
        model="gpt-5.5",
        prompt_hash=prompt,
        response_hash="response",
        tokens_in=tokens,
        tokens_out=tokens * 2,
        latency_ms=1,
        token_source=SOURCE_VENDOR,
    )


def test_cost_and_outage_readers_count_repeat_rows(monkeypatch, capsys) -> None:
    """DLIB-OBS-08: A9 both rows contribute tokens/cost and outage call counts."""
    graph = InMemoryGraphStore()
    first = write_turn(
        graph, corr="sched-x:GILD:defender:r2", prompt="first", tokens=100
    )
    initial = llm_cost_projection(graph, now=datetime.now(tz=UTC))
    repeat = write_turn(
        graph, corr="sched-x:GILD:defender:r2", prompt="repeat", tokens=300
    )
    assert repeat.key == first.key + ":repeat-1"

    costs = llm_cost_projection(graph, now=datetime.now(tz=UTC))
    (model,) = costs["models"]
    (agent,) = costs["agents"]
    assert model["calls"] == agent["calls"] == 2
    assert model["tokens_in"] == agent["tokens_in"] == 400
    assert model["tokens_out"] == agent["tokens_out"] == 800
    assert costs["source_total"] == pytest.approx(initial["source_total"] * 4)
    report = outage_report(graph.list_nodes("LLMCall"))
    assert report.calls == 2
    assert report.silent_calls == 0
    assert report.verdict == "ok"

    monkeypatch.setattr("kernel.graph_env.build_graph_from_env", lambda: graph)
    monkeypatch.setattr("dotenv.load_dotenv", lambda *args, **kwargs: None)
    assert check_llm_outage.main([]) == 0
    assert "ok: 0/2 calls silent" in capsys.readouterr().out


@pytest.mark.parametrize("repeat_first", [False, True])
def test_reproducibility_uses_the_original_in_either_listing_order(
    monkeypatch, repeat_first: bool
) -> None:
    """DLIB-OBS-07: B1 repeat hashes cannot replace the original turn's evidence."""
    graph = InMemoryGraphStore()
    item = intent()
    orders = order_set(item)
    node = linked_graph(graph, full=True)
    node = graph.merge_node(
        "PMRun", node.key, {"order_intent_set": orders.model_dump(mode="json")}
    )
    corr = f"{node.key}:{item.ticker}:defender:r1"
    digest = replayed_prompt_digest(graph, node, orders, item)
    original = write_turn(graph, corr=corr, prompt=digest, tokens=7)
    repeated = write_turn(graph, corr=corr, prompt="different repeat hash", tokens=11)
    list_nodes = graph.list_nodes
    rows = [repeated, original] if repeat_first else [original, repeated]
    monkeypatch.setattr(
        graph,
        "list_nodes",
        lambda label: rows if label == "LLMCall" else list_nodes(label),
    )

    report = measure_reproducibility(graph)

    assert report.outcomes["matched"] == report.compared == 1
    assert report.outcomes["mismatched"] == 0
