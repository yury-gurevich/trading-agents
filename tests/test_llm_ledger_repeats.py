"""Append-only completion proofs for S256.

Agent: kernel
Role: prove repeated correlation IDs preserve every completion's audit facts.
External I/O: none.
"""

from __future__ import annotations

from kernel import InMemoryGraphStore
from kernel.llm_ledger import write_llm_call
from kernel.llm_tokens import SOURCE_VENDOR


def test_each_completion_is_its_own_unchanged_row() -> None:
    """DLIB-OBS-08: A7 three calls return their own row without rewriting one."""
    graph = InMemoryGraphStore()
    nodes = []
    snapshots = []
    for index, tokens in enumerate((7, 11, 17)):
        node = write_llm_call(
            graph,
            calling_agent="deliberator-proponent",
            correlation_id="sched-x:GILD:defender:r2",
            model=f"model-{index}",
            prompt_hash=f"prompt-{index}",
            response_hash=f"response-{index}",
            tokens_in=index + 1,
            tokens_out=tokens,
            latency_ms=100 + index,
            stop_reason=f"stop-{index}",
            cache_read_tokens=index,
            cache_write_tokens=index + 2,
            token_source=SOURCE_VENDOR,
            system_prompt_hash=f"system-{index}",
            prompt_recipe_hash=f"recipe-{index}",
        )
        nodes.append(node)
        snapshots.append(dict(node.props))

    first = "llmcall:deliberator-proponent:sched-x:GILD:defender:r2"
    assert [node.key for node in nodes] == [
        first,
        first + ":repeat-1",
        first + ":repeat-2",
    ]
    rows = graph.list_nodes("LLMCall")
    assert len(rows) == 3
    assert sum(int(row.props["tokens_out"]) for row in rows) == 35
    assert sum(int(row.props["tokens_in"]) for row in rows) == 6
    for index, node in enumerate(nodes):
        stored = graph.get_node("LLMCall", node.key)
        assert stored is not None
        assert dict(stored.props) == snapshots[index]
        assert node.props["model"] == f"model-{index}"
        assert node.props["prompt_hash"] == f"prompt-{index}"
        assert node.props["response_hash"] == f"response-{index}"
        assert node.props["stop_reason"] == f"stop-{index}"
        assert node.props["latency_ms"] == 100 + index
        assert node.props["cache_read_tokens"] == index
        assert node.props["cache_write_tokens"] == index + 2
        assert node.props["system_prompt_hash"] == f"system-{index}"
        assert node.props["prompt_recipe_hash"] == f"recipe-{index}"
        assert set(node.props) == {
            "calling_agent",
            "correlation_id",
            "model",
            "prompt_hash",
            "response_hash",
            "tokens_in",
            "tokens_out",
            "cache_read_tokens",
            "cache_write_tokens",
            "token_source",
            "system_prompt_hash",
            "prompt_recipe_hash",
            "latency_ms",
            "stop_reason",
            "created_at",
        }


def test_repeat_allocation_takes_the_first_free_key() -> None:
    """DLIB-OBS-08: a gap in repeat keys is filled without changing occupied rows."""
    graph = InMemoryGraphStore()
    first = "llmcall:operator:actor:channel:text:repeat-7"
    props = {"tokens_out": 13}
    graph.merge_node("LLMCall", first, props)
    graph.merge_node("LLMCall", first + ":repeat-2", props)

    written = write_llm_call(
        graph,
        calling_agent="operator",
        correlation_id="actor:channel:text:repeat-7",
        model="model",
        prompt_hash="prompt",
        response_hash="response",
        tokens_in=3,
        tokens_out=17,
        latency_ms=1,
    )

    assert written.key == first + ":repeat-1"
    assert dict(graph.get_node("LLMCall", first).props) == props
    assert dict(graph.get_node("LLMCall", first + ":repeat-2").props) == props
