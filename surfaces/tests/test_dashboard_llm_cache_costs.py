"""Cache-aware LLM cost pricing tests.

Agent: surfaces
Role: prove cached tokens are priced at their own rates, and that a total still
      built on word counts says so instead of reading as a measurement.
External I/O: committed pricing JSON is replaced by a fixture; graph is a fake.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from kernel import InMemoryGraphStore
from kernel.llm_tokens import SOURCE_ESTIMATED, SOURCE_VENDOR
from surfaces.dashboard.llm_cost_tokens import CacheRates, cache_rates, read_call_tokens
from surfaces.dashboard.llm_costs import llm_cost_projection

if TYPE_CHECKING:
    from pathlib import Path

NOW = datetime(2026, 9, 13, 12, tzinfo=UTC)
_CATALOGUE: dict[str, object] = {
    "pricing_as_of": "2026-09-13",
    "source_currency": "USD",
    "display_currency": "AUD",
    "fx": {"aud_per_usd": 1.0},
    "cache_multipliers": {"read": 0.1, "write": 1.25},
    "models": {"claude-opus-5": {"input": 5.0, "output": 25.0}},
}


def _pricing(tmp_path: Path, catalogue: dict[str, object]) -> Path:
    path = tmp_path / "llm_pricing.json"
    path.write_text(json.dumps(catalogue), encoding="utf-8")
    return path


def _call(graph: InMemoryGraphStore, key: str, **props: object) -> None:
    graph.merge_node(
        "LLMCall",
        key,
        {
            "model": "claude-opus-5",
            "calling_agent": "deliberator-opponent",
            "created_at": "2026-09-13T01:00:00+00:00",
            "tokens_in": 0,
            "tokens_out": 0,
            **props,
        },
    )


def test_cached_tokens_are_priced_off_the_input_rate_at_their_own_multiplier(
    tmp_path: Path,
) -> None:
    """A cache read is input already paid to write — 0.1x input, never output."""
    graph = InMemoryGraphStore()
    _call(
        graph,
        "cached",
        tokens_in=1_000_000,
        tokens_out=0,
        cache_read_tokens=1_000_000,
        cache_write_tokens=1_000_000,
        token_source=SOURCE_VENDOR,
    )

    result = llm_cost_projection(
        graph, now=NOW, pricing_path=_pricing(tmp_path, _CATALOGUE)
    )

    # 5.00 uncached + 0.50 read + 6.25 write, output free.
    assert result["source_total"] == 11.75
    assert result["estimated_calls"] == 0


def test_caching_is_cheaper_than_not_caching_for_the_same_work(
    tmp_path: Path,
) -> None:
    """The whole point of the marker, expressed as the number it moves."""
    pricing = _pricing(tmp_path, _CATALOGUE)
    cold = InMemoryGraphStore()
    _call(cold, "cold", tokens_in=2_561_000, token_source=SOURCE_VENDOR)
    warm = InMemoryGraphStore()
    _call(warm, "warm", cache_read_tokens=2_561_000, token_source=SOURCE_VENDOR)

    cold_cost = llm_cost_projection(cold, now=NOW, pricing_path=pricing)
    warm_cost = llm_cost_projection(warm, now=NOW, pricing_path=pricing)

    cold_total = Decimal(str(cold_cost["source_total"]))
    warm_total = Decimal(str(warm_cost["source_total"]))
    assert warm_total < cold_total
    assert warm_total == Decimal(str(round(float(cold_total / 10), 6)))


def test_a_total_built_on_word_counts_declares_itself_a_floor(
    tmp_path: Path,
) -> None:
    """🚨 Item 43: pre-S199 rows are estimates and the projection must say so."""
    graph = InMemoryGraphStore()
    _call(graph, "legacy", tokens_in=6, tokens_out=4)  # no token_source at all
    _call(graph, "measured", tokens_in=1731, tokens_out=906, token_source=SOURCE_VENDOR)

    result = llm_cost_projection(
        graph, now=NOW, pricing_path=_pricing(tmp_path, _CATALOGUE)
    )

    assert result["estimated_calls"] == 1
    assert "1 priced call(s) still carry word-count estimates" in str(
        result["coverage_note"]
    )
    (row,) = list(result["models"])  # type: ignore[call-overload]
    assert row["estimated_calls"] == 1
    assert row["calls"] == 2


def test_a_catalogue_without_cache_rates_charges_full_input_price(
    tmp_path: Path,
) -> None:
    """Fail expensive, not free: an unpriced cache must never read as 0 cost."""
    bare = dict(_CATALOGUE)
    del bare["cache_multipliers"]
    graph = InMemoryGraphStore()
    _call(graph, "cached", cache_read_tokens=1_000_000, token_source=SOURCE_VENDOR)

    result = llm_cost_projection(graph, now=NOW, pricing_path=_pricing(tmp_path, bare))

    assert result["source_total"] == 5.0


def test_cache_rates_rejects_a_non_mapping_declaration() -> None:
    assert cache_rates({"cache_multipliers": "0.1"}) == CacheRates(
        read=Decimal(1), write=Decimal(1)
    )


def test_unreadable_token_counts_read_as_zero_not_as_a_crash() -> None:
    tokens = read_call_tokens({"tokens_in": "many", "tokens_out": None})

    assert (tokens.tokens_in, tokens.tokens_out) == (0, 0)
    assert tokens.token_source == SOURCE_ESTIMATED
    assert not tokens.is_vendor_counted
