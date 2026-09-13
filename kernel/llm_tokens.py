"""Vendor-reported token accounting for one LLM completion.

Agent: kernel
Role: carry a provider's own `usage` numbers from an adapter to the ledger in
      one normalised shape, and say plainly when no provider reported any.
External I/O: none.

Exists because the ledger used to write `max(1, len(text.split()))` into
`tokens_in`/`tokens_out` — a *word* count, excluding the system prompt
entirely — and every cost figure this project has published was derived from
it (work-queue item 43, [DL-150](../docs/design-log.md)). That error was not
academic: S173 Part B priced a sweep off those counts, was **3.2x low**, and
the correction was bought for $58 ([DL-160](../docs/design-log.md)).

The honest source is the vendor's own `usage` block. When an adapter reports
one, the ledger records it and stamps ``token_source="vendor"``; when none is
available (the deterministic fake, a provider that withheld it) the estimate
stands but is stamped ``token_source="estimated"``. Both shapes have always
existed in the same table; only the stamp is new, and without it a corrected
row and a word-counted row are indistinguishable — the defect pattern this
repo has now met four times (DL-152).

🪤 **Vendor field names are deliberately not interpreted here.** Each adapter
builds its own ``LLMUsage`` because the two providers disagree on what the
input count *means*: Anthropic's `input_tokens` **excludes** cached tokens and
bills them separately, while OpenAI's `prompt_tokens` **includes** its
`cached_tokens`. Mapping them field-for-field would double-count every cached
OpenAI token. This module fixes the normalised meaning — ``tokens_in`` is
always the *uncached* input — and leaves each adapter to reach it.
"""

from __future__ import annotations

from dataclasses import dataclass

SOURCE_VENDOR = "vendor"
SOURCE_ESTIMATED = "estimated"


@dataclass(frozen=True)
class LLMUsage:
    """One completion's token counts, normalised across providers.

    ``tokens_in`` is the **uncached** input count, so total billed input is
    ``tokens_in + cache_read_tokens + cache_write_tokens``. The three are kept
    apart because they are billed at three different rates (reads ~0.1x, writes
    1.25x for the 5-minute TTL); folding them into one number would replace an
    understated bill with an overstated one.
    """

    tokens_in: int
    tokens_out: int
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0


@dataclass(frozen=True)
class TokenCounts:
    """What the ledger writes, plus the provenance of where it came from."""

    tokens_in: int
    tokens_out: int
    cache_read_tokens: int
    cache_write_tokens: int
    token_source: str


def usage_count(usage: object, path: str) -> int:
    """Read one non-negative integer from a usage object by dotted path.

    A missing, null or unparseable field reads 0 rather than raising: an SDK
    that drops a field from its usage block must not take the veto down.
    """
    current: object = usage
    for part in path.split("."):
        if current is None:
            return 0
        current = getattr(current, part, None)
    if not isinstance(current, int | float | str):
        return 0
    try:
        return max(0, int(current))
    except (TypeError, ValueError):
        return 0


def llm_usage_or_none(
    *,
    tokens_in: int,
    tokens_out: int,
    cache_read_tokens: int = 0,
    cache_write_tokens: int = 0,
) -> LLMUsage | None:
    """Build usage, or None when the provider reported nothing countable.

    An all-zero block means the provider withheld its accounting, so the
    ledger falls back to the stamped estimate instead of recording a confident
    zero that would price as free.
    """
    if not any((tokens_in, tokens_out, cache_read_tokens, cache_write_tokens)):
        return None
    return LLMUsage(
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        cache_read_tokens=cache_read_tokens,
        cache_write_tokens=cache_write_tokens,
    )


def llm_usage(client: object) -> LLMUsage | None:
    """Return the usage a client recorded for its last completion, if any."""
    usage = getattr(client, "last_usage", None)
    return usage if isinstance(usage, LLMUsage) else None


def token_counts(usage: LLMUsage | None, *, prompt: str, response: str) -> TokenCounts:
    """Prefer the vendor's counts; fall back to a stamped word estimate."""
    if usage is not None:
        return TokenCounts(
            tokens_in=usage.tokens_in,
            tokens_out=usage.tokens_out,
            cache_read_tokens=usage.cache_read_tokens,
            cache_write_tokens=usage.cache_write_tokens,
            token_source=SOURCE_VENDOR,
        )
    return TokenCounts(
        tokens_in=rough_tokens(prompt),
        tokens_out=rough_tokens(response),
        cache_read_tokens=0,
        cache_write_tokens=0,
        token_source=SOURCE_ESTIMATED,
    )


def rough_tokens(value: str) -> int:
    """Return the legacy word-count estimate, kept only as the fallback."""
    return max(1, len(value.split())) if value else 0
