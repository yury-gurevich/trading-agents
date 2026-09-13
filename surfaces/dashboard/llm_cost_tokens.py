"""Per-call token reading and cache-aware cost arithmetic.

Agent: surfaces
Role: turn one LLMCall row into billable token groups and price them against
      the pack catalogue, including the two cache rates.
External I/O: none.

Split out of `llm_costs.py` when cache pricing arrived: the projection module
was already at 160 lines and the 200-line hard block is not negotiable. Keeping
the arithmetic here also puts the three rates in one readable place, which is
where the previous generation of this code went wrong — it had exactly two.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping

_MTOK = Decimal(1_000_000)
SOURCE_VENDOR = "vendor"


@dataclass(frozen=True)
class CallTokens:
    """The four billable token groups of one ledger row, plus its provenance."""

    tokens_in: int
    tokens_out: int
    cache_read_tokens: int
    cache_write_tokens: int
    token_source: str

    @property
    def is_vendor_counted(self) -> bool:
        """Return whether these counts came from the provider's own usage."""
        return self.token_source == SOURCE_VENDOR


@dataclass(frozen=True)
class CacheRates:
    """Multipliers applied to a model's input rate for cached tokens."""

    read: Decimal
    write: Decimal


def read_call_tokens(props: Mapping[str, object]) -> CallTokens:
    """Read one LLMCall row's token groups, tolerating pre-S199 rows.

    Rows written before the cache columns existed carry neither them nor
    `token_source`; they read as zero-cache and **estimated**, which is exactly
    what they are. That is the whole reason the stamp is recorded rather than
    inferred — without it these rows would be indistinguishable from a
    vendor-counted call that genuinely had no cache activity.
    """
    return CallTokens(
        tokens_in=_int(props.get("tokens_in")),
        tokens_out=_int(props.get("tokens_out")),
        cache_read_tokens=_int(props.get("cache_read_tokens")),
        cache_write_tokens=_int(props.get("cache_write_tokens")),
        token_source=str(props.get("token_source", "estimated")),
    )


def cache_rates(catalogue: Mapping[str, object]) -> CacheRates:
    """Read the cache multipliers, defaulting to full input price if absent."""
    raw = catalogue.get("cache_multipliers")
    if not isinstance(raw, dict):
        return CacheRates(read=Decimal(1), write=Decimal(1))
    return CacheRates(
        read=Decimal(str(raw.get("read", 1))),
        write=Decimal(str(raw.get("write", 1))),
    )


def source_cost(
    tokens: CallTokens, price: Mapping[str, object], rates: CacheRates
) -> Decimal:
    """Price one row's tokens in the catalogue's source currency.

    Cached tokens are priced off the model's *input* rate scaled by their own
    multiplier, never off the output rate — a cache read is input that was
    already paid to write.
    """
    input_rate = Decimal(str(price["input"]))
    output_rate = Decimal(str(price["output"]))
    return (
        Decimal(tokens.tokens_in) * input_rate
        + Decimal(tokens.cache_read_tokens) * input_rate * rates.read
        + Decimal(tokens.cache_write_tokens) * input_rate * rates.write
        + Decimal(tokens.tokens_out) * output_rate
    ) / _MTOK


def _int(value: object) -> int:
    try:
        return max(0, int(str(value)))
    except (TypeError, ValueError):
        return 0
