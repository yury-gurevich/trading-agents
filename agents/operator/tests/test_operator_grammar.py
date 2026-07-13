"""Operator grammar and helper tests.

Agent: operator
Role: verify intent grammar, prompt schema, result parsing, and evidence lookup.
External I/O: none.
"""

from __future__ import annotations

from agents.operator.domain.evidence import _RUN_CHAIN, _compact, gather_evidence
from agents.operator.domain.grammar import INTENT_FAMILIES, apply_confirmation_policy
from agents.operator.domain.prompts import build_interpret_system
from agents.operator.domain.result import (
    correlation_id,
    intent_from_data,
    message,
    outcome,
    parse_json,
    refused,
    with_graph,
)
from contracts.common import Provenance
from contracts.operator import TypedIntent
from kernel import FakeLLMClient, InMemoryGraphStore, Node


def test_all_intent_families_are_declared_and_prompted() -> None:
    assert set(INTENT_FAMILIES) == {
        "status",
        "explain",
        "approve",
        "reject",
        "modify",
        "run",
        "mode",
        "stage",
        "pause",
        "resume",
    }
    prompt = build_interpret_system()
    for family in INTENT_FAMILIES:
        assert family in prompt


def test_confirmation_policy_overrides_model_value_for_each_family() -> None:
    for family, spec in INTENT_FAMILIES.items():
        intent = TypedIntent(
            family=family,
            parameters={},
            requires_confirmation=not spec.requires_confirmation,
            provenance=Provenance(run_id="r", source_agent="operator"),
        )
        assert (
            apply_confirmation_policy(family, intent).requires_confirmation
            is spec.requires_confirmation
        )


def test_result_helpers_normalize_invalid_or_refused_output() -> None:
    assert parse_json("not-json")["outcome"] == "refused"
    assert parse_json("[]")["outcome"] == "refused"
    assert outcome({"outcome": "bogus"}) == "refused"
    assert message({"reason": "no"}).summary == "no"
    assert refused("blocked").message.summary == "blocked"
    assert intent_from_data({"family": "not-real"}, "corr") is None
    assert intent_from_data({"family": "status", "parameters": "bad"}, "corr")


def test_intent_result_helpers_attach_provenance_and_params() -> None:
    intent = intent_from_data(
        {"family": "run", "parameters": {"stage": "paper", "n": 1}}, "corr"
    )
    assert intent is not None
    assert intent.parameters == {"stage": "paper", "n": "1"}
    assert intent.requires_confirmation is True
    node = Node("Intent", "intent:corr", {})
    updated = with_graph(intent, node)
    assert updated.provenance.graph_node_id == "Intent:intent:corr"
    assert correlation_id("a", "b") == correlation_id("a", "b")


def test_fake_llm_client_keyword_and_default_paths() -> None:
    llm = FakeLLMClient({"run": '{"outcome": "intent", "family": "run"}'})
    assert "run" in llm.complete(system="", user="please run", tool_schema={})
    assert "status" in llm.complete(system="", user="unknown", tool_schema={})


def test_gather_evidence_returns_trade_and_status_nodes() -> None:
    graph = InMemoryGraphStore()
    graph.merge_node("Recommendation", "rec:aapl", {"ticker": "AAPL"})
    graph.merge_node("Recommendation", "rec:aapl2", {"ticker": "AAPL"})
    graph.merge_node("Snapshot", "snapshot:latest", {"run_id": "pm"})
    assert len(gather_evidence(graph, "why AAPL", 1)) == 1
    assert gather_evidence(graph, "system status", 5)[0]["label"] == "Snapshot"
    assert gather_evidence(graph, "why MSFT", 5) == []
    assert gather_evidence(object(), "status", 5) == []  # type: ignore[arg-type]
    assert gather_evidence(_EmptyGraph(), "status", 5) == []  # type: ignore[arg-type]


def test_run_evidence_walks_provenance_and_compacts_prompt_values() -> None:
    graph = InMemoryGraphStore()
    request = graph.merge_node(
        "RunRequest",
        "run-request:run-a",
        {"run_id": "run-a", "tickers": ("AAPL",)},
    )
    current = request
    for index, (edge, label) in enumerate(_RUN_CHAIN):
        props = (
            {"run_id": "run-a", "counts": {"returned": 1}}
            if label == "MarketData"
            else {"run_id": "run-a"}
        )
        child = graph.merge_node(label, f"{label.lower()}:{index}", props)
        graph.add_edge(current, child, edge)
        current = child

    limited = gather_evidence(graph, "Selected run: run-a", 1)
    walked = gather_evidence(graph, "Selected run: run-a", 5)

    assert limited[0]["label"] == "RunRequest"
    assert [row["label"] for row in walked[:2]] == ["RunRequest", "MarketData"]
    assert walked[1]["props"] == {
        "run_id": "run-a",
        "counts": {"returned": 1},
    }
    assert _compact([object()]) == {"item_count": 1}
    assert _compact(list(range(11))) == {"item_count": 11}
    assert str(_compact(object())).startswith("<object object at")


class _EmptyGraph:
    def list_nodes(self, label: str) -> tuple[Node, ...]:
        del label
        return ()
