"""LLM ledger pricing projection for the operations dashboard.

Agent: surfaces
Role: aggregate month-to-date LLMCall tokens against the pack pricing catalogue.
External I/O: reads the injected GraphStore and committed pricing JSON.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from kernel import GraphStore

_PRICING = Path(__file__).parents[2] / "orchestration" / "packs" / "llm_pricing.json"
_MTOK = Decimal(1_000_000)


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
    grouped: dict[str, dict[str, int]] = {}
    for node in graph.list_nodes("LLMCall"):
        created_at = str(node.props.get("created_at", ""))
        if not created_at.startswith(current.strftime("%Y-%m")):
            continue
        model = str(node.props.get("model", "unknown"))
        row = grouped.setdefault(model, {"calls": 0, "tokens_in": 0, "tokens_out": 0})
        row["calls"] += 1
        row["tokens_in"] += int(str(node.props.get("tokens_in", 0)))
        row["tokens_out"] += int(str(node.props.get("tokens_out", 0)))
    source_total = Decimal(0)
    models: list[dict[str, object]] = []
    for model in sorted(grouped):
        usage = grouped[model]
        price = prices.get(model)
        if price is None:
            models.append(
                {"model": model, **usage, "status": "untracked", "cost": None}
            )
            continue
        source_cost = (
            Decimal(usage["tokens_in"]) * Decimal(str(price["input"]))
            + Decimal(usage["tokens_out"]) * Decimal(str(price["output"]))
        ) / _MTOK
        cost = source_cost * aud_per_source
        source_total += source_cost
        models.append(
            {
                "model": model,
                **usage,
                "status": "priced",
                "cost": round(float(cost), 6),
                "source_cost": round(float(source_cost), 6),
            }
        )
    return {
        "pricing_as_of": str(catalogue["pricing_as_of"]),
        "currency": str(catalogue["display_currency"]),
        "source_currency": str(catalogue["source_currency"]),
        "total": round(float(source_total * aud_per_source), 6),
        "source_total": round(float(source_total), 6),
        "fx": fx,
        "models": models,
        "untracked_models": sum(row["status"] == "untracked" for row in models),
        "coverage_note": (
            "Only append-only LLMCall ledger usage is priced; deliberation and "
            "prompt-compilation spend not present in that ledger is untracked."
        ),
    }
