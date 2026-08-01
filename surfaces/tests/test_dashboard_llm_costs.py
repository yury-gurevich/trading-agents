"""Dashboard LLM cost-attribution tests.

Agent: surfaces
Role: prove LLMCall pricing remains attributable across shared writers.
External I/O: committed pricing JSON only; graph reads are fakes.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast

from kernel import InMemoryGraphStore
from surfaces.dashboard.llm_costs import llm_cost_projection

NOW = datetime(2026, 7, 10, 12, tzinfo=UTC)


def _llm_node(
    graph: InMemoryGraphStore,
    key: str,
    model: str,
    tokens_in: int,
    tokens_out: int,
    created_at: str = "2026-07-10T01:00:00+00:00",
    calling_agent: str = "operator",
) -> None:
    graph.merge_node(
        "LLMCall",
        key,
        {
            "model": model,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "created_at": created_at,
            "calling_agent": calling_agent,
        },
    )


def test_pricing_known_tokens_and_unknown_model_is_untracked() -> None:
    graph = InMemoryGraphStore()
    _llm_node(graph, "known", "gpt-5.5", 1_000_000, 1_000_000)
    _llm_node(
        graph,
        "unknown",
        "future-model",
        7,
        9,
        calling_agent="deliberator-manager",
    )
    _llm_node(
        graph,
        "old",
        "gpt-5.5",
        1_000_000,
        1_000_000,
        "2026-06-30T23:59:00+00:00",
    )
    result = llm_cost_projection(graph, now=NOW)
    rows = {row["model"]: row for row in cast("list[dict[str, Any]]", result["models"])}
    assert rows["gpt-5.5"]["source_cost"] == 35.0
    assert rows["gpt-5.5"]["cost"] == 48.807698
    assert rows["future-model"]["status"] == "untracked"
    assert rows["future-model"]["cost"] is None
    assert result["total"] == 48.807698
    assert result["currency"] == "AUD"
    assert cast("dict[str, Any]", result["fx"])["bank"] == (
        "Commonwealth Bank of Australia"
    )
    assert result["untracked_models"] == 1
    assert "calling_agent" in str(result["coverage_note"])
    agents = {
        row["calling_agent"]: row
        for row in cast("list[dict[str, Any]]", result["agents"])
    }
    assert agents["operator"]["source_cost"] == 35.0
    assert agents["deliberator-manager"]["untracked_calls"] == 1
