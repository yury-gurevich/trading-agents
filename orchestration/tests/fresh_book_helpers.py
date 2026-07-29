"""Fresh-book integration test helpers.

Agent: orchestration
Role: build compact graph fixtures for position-sync-to-analyst tests.
External I/O: none.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from agents.analyst.tests.helpers import bars
from contracts.common import Provenance
from contracts.provider import (
    MARKET_DATA_LABEL,
    REGIME_CONTEXT_LABEL,
    DataQualityTrace,
    MarketData,
    RegimeContext,
)
from orchestration.start import place_run_request

if TYPE_CHECKING:
    from contracts.scanner import CandidateSet
    from kernel import InMemoryGraphStore, Node


def scan(graph: InMemoryGraphStore, run_id: str, payload: CandidateSet) -> Node:
    place_run_request(graph, run_id=run_id, tickers=("AAPL", "MSFT"))
    scan_node = graph.merge_node(
        "ScanRun", f"scan:{run_id}", {"candidate_set": payload.model_dump(mode="json")}
    )
    market = graph.merge_node(
        MARKET_DATA_LABEL,
        f"market-data:{run_id}",
        {
            "snapshot": _market_data().model_dump(mode="json"),
            "window_end": "2026-07-28",
            "run_id": run_id,
        },
    )
    graph.add_edge(scan_node, market, "DERIVED_FROM")
    graph.merge_node(
        REGIME_CONTEXT_LABEL,
        f"regime-context:{run_id}",
        {"snapshot": _regime().model_dump(mode="json"), "run_id": run_id},
    )
    return scan_node


def snapshot(
    graph: InMemoryGraphStore,
    run_id: str,
    *,
    status: str = "fresh",
    holdings: tuple[object, ...] = (),
    reason: str | None = None,
) -> Node:
    props: dict[str, object] = {
        "run_id": run_id,
        "status": status,
        "created_at": "2026-07-28T00:00:00+00:00",
        "holding_count": len(holdings),
        "holdings": list(holdings),
    }
    if reason:
        props["stale_reason"] = reason
    return graph.merge_node("BrokerPositionSnapshot", f"snapshot:{run_id}", props)


def position(
    graph: InMemoryGraphStore,
    key: str,
    ticker: str,
    quantity: int,
    opened_price_cents: int,
) -> None:
    graph.merge_node(
        "Position",
        key,
        {
            "run_id": "pm-run",
            "ticker": ticker,
            "opened_price_cents": opened_price_cents,
            "quantity": quantity,
            "stop_pct": 0.05,
            "target_pct": 0.10,
            "horizon_days": 14,
            "opened_at": "2026-07-28T00:00:00+00:00",
            "status": "open",
            "degraded": False,
        },
    )


def holding(ticker: str, quantity: int, avg_entry_cents: int) -> dict[str, object]:
    return {
        "ticker": ticker,
        "quantity": quantity,
        "avg_entry_cents": avg_entry_cents,
        "market_value_cents": quantity * avg_entry_cents,
    }


def analyst_run(graph: InMemoryGraphStore) -> Node:
    return graph.list_nodes("AnalystRun")[0]


def recommendation_set(graph: InMemoryGraphStore) -> Mapping[str, Any]:
    raw = analyst_run(graph).props["recommendation_set"]
    assert isinstance(raw, Mapping)
    return raw


def _market_data() -> MarketData:
    return MarketData(
        bars=bars(),
        quality=DataQualityTrace(requested=3, returned=3),
        provenance=Provenance(run_id="provider-md", source_agent="provider"),
    )


def _regime() -> RegimeContext:
    return RegimeContext(
        label="neutral",
        as_of=datetime.now(tz=UTC),
        base_min_confidence=0.55,
        base_stop_loss_pct=0.05,
        base_take_profit_pct=0.10,
        base_max_holding_days=10,
        provenance=Provenance(run_id="provider-rg", source_agent="provider"),
    )
