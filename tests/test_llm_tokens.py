"""Vendor token-accounting port tests.

Agent: kernel
Role: prove a provider's own usage reaches the ledger, and that an absent or
      malformed usage block degrades to a *stamped* estimate rather than a
      confident zero.
External I/O: none.
"""

from __future__ import annotations

from types import SimpleNamespace

from kernel.llm_tokens import (
    SOURCE_ESTIMATED,
    SOURCE_VENDOR,
    LLMUsage,
    llm_usage,
    llm_usage_or_none,
    rough_tokens,
    token_counts,
    usage_count,
)


def test_usage_count_reads_a_dotted_path() -> None:
    usage = SimpleNamespace(prompt_tokens_details=SimpleNamespace(cached_tokens=2048))

    assert usage_count(usage, "prompt_tokens_details.cached_tokens") == 2048


def test_usage_count_treats_every_unreadable_shape_as_zero() -> None:
    """A provider that drops a usage field must not take the veto down."""
    assert usage_count(None, "input_tokens") == 0
    assert usage_count(SimpleNamespace(), "input_tokens") == 0
    assert usage_count(SimpleNamespace(a=None), "a.b") == 0
    assert usage_count(SimpleNamespace(input_tokens="many"), "input_tokens") == 0
    assert usage_count(SimpleNamespace(input_tokens=-5), "input_tokens") == 0


def test_all_zero_usage_is_no_usage_at_all() -> None:
    """An empty block must fall back to the estimate, not price as free."""
    assert llm_usage_or_none(tokens_in=0, tokens_out=0) is None
    cache_only = llm_usage_or_none(tokens_in=0, tokens_out=0, cache_read_tokens=9)
    assert cache_only == LLMUsage(tokens_in=0, tokens_out=0, cache_read_tokens=9)


def test_llm_usage_reads_only_a_real_usage_attribute() -> None:
    recorded = LLMUsage(tokens_in=10, tokens_out=20)

    assert llm_usage(SimpleNamespace(last_usage=recorded)) is recorded
    assert llm_usage(SimpleNamespace()) is None
    assert llm_usage(SimpleNamespace(last_usage={"tokens_in": 10})) is None


def test_vendor_counts_are_recorded_and_stamped_as_vendor() -> None:
    usage = LLMUsage(
        tokens_in=1200, tokens_out=800, cache_read_tokens=2400, cache_write_tokens=50
    )

    counts = token_counts(usage, prompt="four words go here", response="one")

    assert counts.tokens_in == 1200
    assert counts.tokens_out == 800
    assert counts.cache_read_tokens == 2400
    assert counts.cache_write_tokens == 50
    assert counts.token_source == SOURCE_VENDOR


def test_absent_usage_falls_back_to_a_word_count_that_says_so() -> None:
    """Item 43: the estimate may survive, but never disguised as a measurement."""
    counts = token_counts(None, prompt="four words go here", response="two words")

    assert (counts.tokens_in, counts.tokens_out) == (4, 2)
    assert counts.cache_read_tokens == 0
    assert counts.cache_write_tokens == 0
    assert counts.token_source == SOURCE_ESTIMATED


def test_rough_tokens_floors_nonempty_text_at_one() -> None:
    assert rough_tokens("") == 0
    assert rough_tokens("   ") == 1
