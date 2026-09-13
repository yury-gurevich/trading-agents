"""LLMCall ledger token-provenance tests.

Agent: kernel
Role: prove the ledger records the provider's own usage when it has one, the
      stamped estimate when it does not, and never the reverse.
External I/O: none.
"""

from __future__ import annotations

from kernel import InMemoryGraphStore
from kernel.llm_ledger import record_llm_call, write_llm_call
from kernel.llm_tokens import SOURCE_ESTIMATED, SOURCE_VENDOR, LLMUsage


def _record(usage: LLMUsage | None) -> dict[str, object]:
    graph = InMemoryGraphStore()
    with record_llm_call(
        graph,
        calling_agent="deliberator-proponent",
        correlation_id="run:TICK:defender:r1",
        model="claude-opus-5",
        prompt="a prompt of six whole words",
    ) as call:
        call.set_response("a four word answer")
        call.set_usage(usage)
    key = "llmcall:deliberator-proponent:run:TICK:defender:r1"
    node = graph.get_node("LLMCall", key)
    assert node is not None
    return dict(node.props)


def test_ledger_records_the_vendors_own_counts() -> None:
    """DLIB-OBS-05: a recorded cost is the provider's number, not our guess."""
    props = _record(
        LLMUsage(
            tokens_in=1731,
            tokens_out=906,
            cache_read_tokens=2561,
            cache_write_tokens=0,
        )
    )

    assert props["tokens_in"] == 1731
    assert props["tokens_out"] == 906
    assert props["cache_read_tokens"] == 2561
    assert props["cache_write_tokens"] == 0
    assert props["token_source"] == SOURCE_VENDOR


def test_ledger_stamps_a_word_count_as_estimated() -> None:
    """DLIB-OBS-05: the fallback is allowed; passing it off as measured is not."""
    props = _record(None)

    assert props["tokens_in"] == 6
    assert props["tokens_out"] == 4
    assert props["token_source"] == SOURCE_ESTIMATED


def test_vendor_and_estimated_rows_are_distinguishable() -> None:
    """The whole point of the stamp: the same table holds both shapes.

    Six words in, four out is also a plausible *vendor* count, so without
    `token_source` these two rows would be byte-identical on the numbers and a
    reader could not tell a measured row from a word count. That is DL-152's
    pattern, and it is what made every pre-S199 cost figure unfalsifiable.
    """
    vendor = _record(LLMUsage(tokens_in=6, tokens_out=4))
    estimated = _record(None)

    numeric = ("tokens_in", "tokens_out", "cache_read_tokens", "cache_write_tokens")
    assert all(vendor[field] == estimated[field] for field in numeric)
    assert vendor["token_source"] != estimated["token_source"]


def test_write_llm_call_defaults_to_estimated_not_vendor() -> None:
    """A caller that forgets the stamp must not be credited with a measurement."""
    graph = InMemoryGraphStore()

    node = write_llm_call(
        graph,
        calling_agent="operator",
        correlation_id="corr",
        model="claude-opus-5",
        prompt_hash="p",
        response_hash="r",
        tokens_in=10,
        tokens_out=20,
        latency_ms=5,
    )

    assert node.props["token_source"] == SOURCE_ESTIMATED
    assert node.props["cache_read_tokens"] == 0
    assert node.props["cache_write_tokens"] == 0
