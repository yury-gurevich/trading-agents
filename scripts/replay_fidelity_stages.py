"""Replay each S237 stage through the fleet's own composition of it.

Agent: tooling
Role: run the scanner's poll step, the analyst's `run_analysis` and the PM's
      `run_evaluation` on exported live inputs; their writes land in a scratch store.
External I/O: reads the trading pack's issuer map.
"""

from __future__ import annotations

from functools import cache
from pathlib import Path
from typing import TYPE_CHECKING

from agents.analyst.run import run_analysis
from agents.portfolio_manager.issuer_map import load_issuer_map
from agents.portfolio_manager.run import run_evaluation
from agents.scanner.poll import scan_market_node
from contracts.scanner import CandidateSet
from kernel import CollectingFaultSink
from kernel.graph_memory import InMemoryGraphStore

if TYPE_CHECKING:
    from collections.abc import Mapping

    from scripts.replay_fidelity_inputs import SessionInputs
    from scripts.replay_settings import ReplaySettings

    from contracts.analyst import RecommendationSet
    from contracts.portfolio_manager import OrderIntentSet
    from contracts.provider import MarketData

_ROOT = Path(__file__).resolve().parents[1]
# The live PM receives this pack file at deploy (issuer_map.py); it is decision input.
ISSUER_MAP_PATH = _ROOT / "orchestration" / "packs" / "trading_issuer_map.json"


@cache
def issuer_map() -> Mapping[str, str]:
    """The pack's ticker -> issuer map, as the live PM loads it."""
    return load_issuer_map(str(ISSUER_MAP_PATH))


def replay_scanner(
    inputs: SessionInputs, settings: ReplaySettings, market: MarketData | None = None
) -> CandidateSet | None:
    """Scan the stored MarketData node exactly as `scan_market_node` does live."""
    snapshot = market if market is not None else inputs.market
    if snapshot is None or not inputs.tickers or inputs.window_end is None:
        return None
    store = InMemoryGraphStore()
    node = store.merge_node(
        "MarketData",
        f"market-data:{inputs.run_id}",
        {
            "snapshot": snapshot.model_dump(mode="json"),
            "tickers": list(inputs.tickers),
            "window_end": inputs.window_end.isoformat(),
            "run_id": inputs.run_id,
        },
    )
    scan_market_node(node, graph=store, settings=settings.scanner)
    scan = next(iter(store.descendants(node, max_depth=1, edge_types={"SCANNED_BY"})))
    return CandidateSet.model_validate(scan.props["candidate_set"])


def replay_analyst(
    inputs: SessionInputs,
    settings: ReplaySettings,
    candidate_set: CandidateSet | None = None,
    market: MarketData | None = None,
) -> RecommendationSet | None:
    """Score the given (by default the live) CandidateSet with `run_analysis`.

    The scratch store holds no Position or stop facts, so the held-stop inputs read
    empty: they are `not_persisted` (DL-238 D4), never guessed.
    """
    candidates = candidate_set if candidate_set is not None else inputs.candidate_set
    snapshot = market if market is not None else inputs.market
    if candidates is None or snapshot is None or inputs.regime is None:
        return None
    return run_analysis(
        InMemoryGraphStore(),
        candidates,
        snapshot,
        inputs.regime,
        settings.analyst,
        CollectingFaultSink(),
        held_positions=inputs.held,
    )


def replay_pm(
    inputs: SessionInputs,
    settings: ReplaySettings,
    recommendation_set: RecommendationSet | None = None,
    market: MarketData | None = None,
) -> OrderIntentSet | None:
    """Size and gate the given (by default the live) set with `run_evaluation`."""
    recommendations = (
        recommendation_set
        if recommendation_set is not None
        else inputs.recommendation_set
    )
    snapshot = market if market is not None else inputs.market
    if recommendations is None or snapshot is None or inputs.regime is None:
        return None
    return run_evaluation(
        InMemoryGraphStore(),
        recommendation_set=recommendations,
        market=snapshot,
        regime=inputs.regime,
        correlation_market=snapshot,
        settings=settings.portfolio,
        portfolio=inputs.portfolio,
        sink=CollectingFaultSink(),
        issuer_map=issuer_map(),
    )
