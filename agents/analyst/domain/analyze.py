"""Analyst batch-scoring pipeline.

Agent: analyst
Role: score a full CandidateSet against market data, regime, and benchmarks;
      group OHLCV bars by ticker for per-candidate lookups.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.analyst.domain.recommend import AnalysisDecision, decide
from agents.analyst.domain.scoring import score_candidate
from kernel.errors import fault_boundary

if TYPE_CHECKING:
    from agents.analyst.settings import AnalystSettings
    from contracts.provider import MarketData, OHLCVBar, RegimeContext
    from contracts.scanner import CandidateSet
    from kernel import FaultSink


def score_candidates(
    candidate_set: CandidateSet,
    market: MarketData,
    regime: RegimeContext,
    benchmark_bars: tuple[OHLCVBar, ...],
    settings: AnalystSettings,
    sink: FaultSink,
) -> tuple[AnalysisDecision, ...] | None:
    """Score all candidates; returns None when the scoring step faults."""
    decisions: tuple[AnalysisDecision, ...] = ()
    with fault_boundary(
        sink,
        agent="analyst",
        module="agents.analyst.agent",
        capability="analyze",
        reraise=False,
    ) as capture:
        bars = _bars_by_ticker(market.bars)
        decisions = tuple(
            decide(
                candidate,
                score_candidate(
                    candidate,
                    bars.get(candidate.ticker, ()),
                    market.fundamentals.get(candidate.ticker, {}),
                    benchmark_bars,
                    market.news.get(candidate.ticker, ()),
                    settings,
                ),
                regime,
            )
            for candidate in candidate_set.candidates
        )
    return None if capture.fault is not None else decisions


def _bars_by_ticker(bars: tuple[OHLCVBar, ...]) -> dict[str, tuple[OHLCVBar, ...]]:
    grouped: dict[str, list[OHLCVBar]] = {}
    for bar in bars:
        grouped.setdefault(bar.ticker, []).append(bar)
    return {ticker: tuple(rows) for ticker, rows in grouped.items()}
