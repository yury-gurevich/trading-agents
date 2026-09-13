"""LLM ledger pricing projection for the operations dashboard.

Agent: surfaces
Role: aggregate month-to-date LLMCall tokens against the pack pricing catalogue.
External I/O: reads the injected GraphStore and committed pricing JSON.

🚨 Every figure this module produced before S199 was understated, because the
ledger it reads wrote *word counts* into `tokens_in`/`tokens_out` and excluded
the system prompt entirely (work-queue item 43, DL-150). The ledger now records
the provider's own `usage`, and each row says which it is — so this projection
reports `estimated_calls` beside the total rather than blending the two
silently. A total with a non-zero `estimated_calls` is a floor, not a price.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING, Any, TypedDict, cast

from surfaces.dashboard.llm_cost_tokens import (
    CacheRates,
    CallTokens,
    cache_rates,
    read_call_tokens,
    source_cost,
)

if TYPE_CHECKING:
    from kernel import GraphStore

_PRICING = Path(__file__).parents[2] / "orchestration" / "packs" / "llm_pricing.json"


class _Usage(TypedDict):
    """Mutable pricing accumulator, per model or per calling agent."""

    calls: int
    tokens_in: int
    tokens_out: int
    cache_read_tokens: int
    cache_write_tokens: int
    estimated_calls: int
    source_cost: Decimal
    untracked_calls: int


def llm_cost_projection(
    graph: GraphStore,
    *,
    now: datetime | None = None,
    pricing_path: Path = _PRICING,
) -> dict[str, object]:
    """Price MTD ledger tokens; missing models remain explicitly untracked."""
    current = now or datetime.now(tz=UTC)
    catalogue = cast(
        "dict[str, Any]", json.loads(pricing_path.read_text(encoding="utf-8"))
    )
    prices = cast("dict[str, dict[str, object]]", catalogue["models"])
    fx = cast("dict[str, object]", catalogue["fx"])
    aud_per_source = Decimal(str(fx["aud_per_usd"]))
    rates = cache_rates(catalogue)
    models: dict[str, _Usage] = {}
    agents: dict[str, _Usage] = {}
    for node in graph.list_nodes("LLMCall"):
        if not str(node.props.get("created_at", "")).startswith(
            current.strftime("%Y-%m")
        ):
            continue
        tokens = read_call_tokens(node.props)
        price = prices.get(str(node.props.get("model", "unknown")))
        for bucket, name in (
            (models, str(node.props.get("model", "unknown"))),
            (agents, str(node.props.get("calling_agent", "unknown"))),
        ):
            _accumulate(bucket, name, tokens=tokens, price=price, rates=rates)
    return _projection(catalogue, fx, aud_per_source, models, agents, prices)


def _projection(
    catalogue: dict[str, Any],
    fx: dict[str, object],
    aud_per_source: Decimal,
    models: dict[str, _Usage],
    agents: dict[str, _Usage],
    prices: dict[str, dict[str, object]],
) -> dict[str, object]:
    model_rows = [
        {
            "model": name,
            **_row(models[name]),
            "status": "priced" if name in prices else "untracked",
            "cost": (
                round(float(models[name]["source_cost"] * aud_per_source), 6)
                if name in prices
                else None
            ),
            "source_cost": round(float(models[name]["source_cost"]), 6),
        }
        for name in sorted(models)
    ]
    source_total = sum(
        (models[name]["source_cost"] for name in models if name in prices), Decimal(0)
    )
    estimated = sum(usage["estimated_calls"] for usage in models.values())
    return {
        "pricing_as_of": str(catalogue["pricing_as_of"]),
        "currency": str(catalogue["display_currency"]),
        "source_currency": str(catalogue["source_currency"]),
        "total": round(float(source_total * aud_per_source), 6),
        "source_total": round(float(source_total), 6),
        "fx": fx,
        "models": model_rows,
        "agents": [
            {
                "calling_agent": name,
                **_row(agents[name]),
                **_costs(agents[name], aud_per_source),
            }
            for name in sorted(agents)
        ],
        "untracked_models": sum(row["status"] == "untracked" for row in model_rows),
        "estimated_calls": estimated,
        "coverage_note": (
            "Append-only LLMCall ledger usage is priced and attributed by "
            "calling_agent; model calls absent from that ledger are untracked. "
            f"{estimated} priced call(s) still carry word-count estimates rather "
            "than vendor token counts, so the total is a floor for those rows."
        ),
    }


def _accumulate(
    bucket: dict[str, _Usage],
    name: str,
    *,
    tokens: CallTokens,
    price: dict[str, object] | None,
    rates: CacheRates,
) -> None:
    row = bucket.setdefault(
        name,
        {
            "calls": 0,
            "tokens_in": 0,
            "tokens_out": 0,
            "cache_read_tokens": 0,
            "cache_write_tokens": 0,
            "estimated_calls": 0,
            "source_cost": Decimal(0),
            "untracked_calls": 0,
        },
    )
    row["calls"] += 1
    row["tokens_in"] += tokens.tokens_in
    row["tokens_out"] += tokens.tokens_out
    row["cache_read_tokens"] += tokens.cache_read_tokens
    row["cache_write_tokens"] += tokens.cache_write_tokens
    if not tokens.is_vendor_counted:
        row["estimated_calls"] += 1
    if price is None:
        row["untracked_calls"] += 1
        return
    row["source_cost"] += source_cost(tokens, price, rates)


def _row(usage: _Usage) -> dict[str, object]:
    return {
        "calls": usage["calls"],
        "tokens_in": usage["tokens_in"],
        "tokens_out": usage["tokens_out"],
        "cache_read_tokens": usage["cache_read_tokens"],
        "cache_write_tokens": usage["cache_write_tokens"],
        "estimated_calls": usage["estimated_calls"],
        "untracked_calls": usage["untracked_calls"],
    }


def _costs(usage: _Usage, aud_per_source: Decimal) -> dict[str, object]:
    return {
        "cost": round(float(usage["source_cost"] * aud_per_source), 6),
        "source_cost": round(float(usage["source_cost"]), 6),
    }
