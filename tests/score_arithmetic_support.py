"""Recorded inputs and synthetic graph lineage for S255.

Agent: testing
Role: supply arithmetic proofs with frozen orders and in-memory packet inputs.
External I/O: local fixture reads only.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from tests.veto_context_fixtures import candidates, intent, order_set, recs
from tests.veto_context_provider_fixtures import market_data

from agents.deliberator.context import build_veto_context
from contracts.analyst import Recommendation, RecommendationSet
from contracts.common import Provenance
from contracts.provider import RegimeContext
from kernel import InMemoryGraphStore

FIXTURE = Path(__file__).parent / "fixtures" / "score_arithmetic_nine_orders.json"
MAIN_PACKETS = FIXTURE.with_name("score_arithmetic_main_packets.json")


def fixture() -> dict:
    """Load the planner's recorded, corrected nine-order fixture."""
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def recorded_order(index: int = 0) -> tuple[Recommendation, RegimeContext]:
    """Validate one recorded order with both additive contract fields."""
    data = fixture()
    order = data["orders"][index]
    rec = Recommendation.model_validate(
        {**order["recommendation"], "score_arithmetic": order["score_arithmetic"]}
    )
    regime = RegimeContext.model_validate(
        {
            "label": "neutral",
            "as_of": datetime(2026, 10, 5, tzinfo=UTC),
            "base_min_confidence": order["base_min_confidence"],
            "base_stop_loss_pct": 0.05,
            "base_take_profit_pct": 0.10,
            "base_max_holding_days": 10,
            "provenance": Provenance(run_id="s255", source_agent="provider"),
            "vix_thresholds": data["vix_thresholds"],
        }
    )
    return rec, regime


def packet(
    rec: Recommendation | None,
    regime: RegimeContext | None,
    *,
    missing: Literal["scan", "market"] | None = None,
) -> str:
    """Render an in-memory lineage, optionally cutting one upstream link."""
    graph = InMemoryGraphStore()
    market = graph.merge_node(
        "MarketData", "market", {"run_id": "market", "snapshot": market_data(True)}
    )
    if regime is not None:
        graph.merge_node(
            "RegimeContext",
            "regime-context:market",
            {"snapshot": regime.model_dump(mode="json")},
        )
    scan = graph.merge_node("ScanRun", "scan", {"candidate_set": candidates()})
    if missing != "market":
        graph.add_edge(scan, market, "DERIVED_FROM")
    recommendations = RecommendationSet.model_validate(recs()).model_copy(
        update={"recommendations": () if rec is None else (rec,)}
    )
    analyst = graph.merge_node(
        "AnalystRun",
        "analyst",
        {"recommendation_set": recommendations.model_dump(mode="json")},
    )
    if missing != "scan":
        graph.add_edge(scan, analyst, "ANALYZED_BY")
    pm = graph.merge_node("PMRun", "pm", {})
    graph.add_edge(analyst, pm, "EVALUATED_BY")
    item = intent().model_copy(update={"ticker": "AAPL" if rec is None else rec.ticker})
    return build_veto_context(graph, pm, order_set(item), item)
