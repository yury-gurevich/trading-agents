"""Barrier settlement test helpers (S241): claims and runs in the graph.

Agent: forecaster
Role: write claims through the forecaster's own claim store, and AnalystRuns whose
      lineage reaches the run's MarketData the way the provider, scanner and
      analyst link them (AnalystRun <-ANALYZED_BY- ScanRun -DERIVED_FROM->
      MarketData). The bar paths are in `settlement_paths.py`.
External I/O: none.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
from typing import TYPE_CHECKING

from agents.forecaster.barrier_store import BarrierClaim, write_claim
from agents.forecaster.domain.barrier_garch import GarchParams
from agents.forecaster.tests.settlement_paths import AS_OF, ENTRY, STOP, TARGET
from contracts.analyst import RecommendationSet
from contracts.common import Explanation, Provenance
from contracts.provider import DataQualityTrace, MarketData

if TYPE_CHECKING:
    from contracts.provider import OHLCVBar
    from kernel import GraphStore, Node

PROBABILITIES = (0.3, 0.5, 0.2)
_PARAMS = GarchParams(mu=0.02, omega=0.05, alpha=0.05, beta=0.90, status="accepted")


def seed_claim(
    graph: GraphStore,
    *,
    ticker: str = "AAPL",
    as_of: date = AS_OF,
    entry_close: float = ENTRY,
    stop_pct: float = STOP,
    target_pct: float = TARGET,
    probabilities: tuple[float, float, float] = PROBABILITIES,
) -> Node:
    """Write one claim through the forecaster's own claim store (S239's schema)."""
    return write_claim(
        graph,
        BarrierClaim(
            ticker=ticker,
            as_of=as_of,
            entry_close=entry_close,
            stop_pct=stop_pct,
            target_pct=target_pct,
            probabilities=probabilities,
            params=_PARAMS,
            history_bars=760,
            n_paths=1000,
            seed=7,
            history_ref=f"barrier-history:claim-{as_of.isoformat()}",
            sessions_requested=760,
        ),
    )


def seed_run(
    graph: GraphStore,
    run_key: str,
    *,
    bars: tuple[OHLCVBar, ...] = (),
    created: date | datetime = AS_OF + timedelta(days=14),
    lineage: bool = True,
) -> Node:
    """An AnalystRun created at ``created`` whose lineage reaches its MarketData.

    The default date is fixed, never the wall clock, so no claim ages past a
    threshold because the suite ran later. The run holds an empty RecommendationSet
    (no buy, so no BarrierHistory is awaited). ``lineage=False`` writes it alone.
    """
    stamp = (
        created
        if isinstance(created, datetime)
        else datetime.combine(created, time(23, 0), tzinfo=UTC)
    )
    run = graph.merge_node(
        "AnalystRun",
        run_key,
        {
            "recommendation_set": _empty_set(run_key).model_dump(mode="json"),
            "created_at": stamp.isoformat(),
        },
    )
    if lineage:
        link_market(graph, run, bars)
    return run


def link_market(graph: GraphStore, run: Node, bars: tuple[OHLCVBar, ...]) -> Node:
    """Write the run's MarketData and the ScanRun that links it to the run."""
    market = MarketData(
        bars=bars,
        quality=DataQualityTrace(
            requested=len({b.ticker for b in bars}),
            returned=len({b.ticker for b in bars}),
        ),
        provenance=Provenance(run_id=run.key, source_agent="provider"),
    )
    market_node = graph.merge_node(
        "MarketData",
        f"market-data:{run.key}",
        {"snapshot": market.model_dump(mode="json"), "run_id": run.key},
    )
    scan = graph.merge_node("ScanRun", f"scan-{run.key}", {"run_id": run.key})
    graph.add_edge(scan, market_node, "DERIVED_FROM")
    graph.add_edge(scan, run, "ANALYZED_BY")
    return market_node


def _empty_set(run_key: str) -> RecommendationSet:
    return RecommendationSet(
        run_id=run_key,
        recommendations=(),
        rejections=(),
        explanation=Explanation(summary="fixture run"),
        provenance=Provenance(run_id=run_key, source_agent="analyst"),
    )
