"""The OpenAI adapter normalises its usage block before the ledger sees it.

Agent: deliberator
Role: pin the one place the two vendors disagree — whether the input count
      already includes cached tokens — so a cached token is never billed twice.
External I/O: none — the SDK is faked; no vendor is contacted.

Split from `test_llm_openai_adapter.py`, which pins the wire shape; this file
pins what comes back.
"""

from __future__ import annotations

import types

from agents.deliberator.llm_openai import _usage


def _response(
    prompt_tokens: int, completion_tokens: int, cached_tokens: int | None = None
) -> object:
    details = (
        types.SimpleNamespace(cached_tokens=cached_tokens)
        if cached_tokens is not None
        else None
    )
    return types.SimpleNamespace(
        usage=types.SimpleNamespace(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            prompt_tokens_details=details,
        )
    )


def test_cached_tokens_are_subtracted_from_the_input_count() -> None:
    """DLIB-OBS-05: `prompt_tokens` includes cached tokens on this vendor.

    Anthropic's `input_tokens` *excludes* them. Mapping the field straight
    across would count every cached token twice and overstate the bill the
    ledger was just corrected to report honestly — so the kernel's `tokens_in`
    is defined as uncached input and this adapter subtracts to reach it.
    """
    usage = _usage(_response(3000, 900, cached_tokens=2048))

    assert usage is not None
    assert usage.tokens_in == 952
    assert usage.cache_read_tokens == 2048
    assert usage.tokens_in + usage.cache_read_tokens == 3000


def test_openai_never_reports_a_cache_write_charge() -> None:
    """Its prompt caching is automatic and unbilled — a real 0, not a gap."""
    usage = _usage(_response(3000, 900, cached_tokens=2048))

    assert usage is not None
    assert usage.cache_write_tokens == 0


def test_absent_cache_details_leave_the_whole_prompt_uncached() -> None:
    usage = _usage(_response(1200, 400))

    assert usage is not None
    assert usage.tokens_in == 1200
    assert usage.cache_read_tokens == 0


def test_more_cached_than_prompt_tokens_cannot_go_negative() -> None:
    """A vendor inconsistency must not produce a negative token count."""
    usage = _usage(_response(100, 50, cached_tokens=500))

    assert usage is not None
    assert usage.tokens_in == 0
    assert usage.cache_read_tokens == 100


def test_no_usage_block_reports_none() -> None:
    assert _usage(types.SimpleNamespace()) is None
