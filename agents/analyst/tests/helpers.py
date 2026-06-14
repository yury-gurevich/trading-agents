"""Analyst test helpers.

Agent: analyst
Role: provide deterministic fixtures for analyst and P2 slice tests.
External I/O: none.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from agents.analyst import AnalystAgent
from agents.provider import ProviderAgent
from agents.provider.settings import ProviderSettings
from agents.provider.sources import FakeDataSource
from contracts.analyst import Recommendation
from contracts.common import Explanation, Provenance
from contracts.provider import OHLCVBar
from contracts.scanner import Candidate, CandidateSet, FilterTrace
from kernel import AgentMessage, CollectingFaultSink, InMemoryGraphStore, InProcessBus

if TYPE_CHECKING:
    from agents.analyst.settings import AnalystSettings


def bar(ticker: str, days_ago: int, close: float, volume: int = 1_000_000) -> OHLCVBar:
    day = datetime.now(tz=UTC).date() - timedelta(days=days_ago)
    open_ = close * 0.95
    return OHLCVBar(
        ticker=ticker,
        bar_date=day,
        open=open_,
        high=max(open_, close) + 1.0,
        low=min(open_, close) - 1.0,
        close=close,
        volume=volume,
    )


def bars() -> tuple[OHLCVBar, ...]:
    # Two bars per ticker: below every indicator window (RSI-2 needs three closes), so
    # the analyst composite fully degrades to neutral -> confidence 0.60, which clears
    # the strict-``<`` regime floor and yields a clean happy-path AAPL recommendation.
    # AAPL's wider rise keeps it the top scanner candidate by relative strength.
    return (
        bar("AAPL", 4, 100.0),
        bar("AAPL", 0, 116.0),
        bar("LOW", 4, 100.0),
        bar("LOW", 0, 101.0),
        bar("MSFT", 4, 100.0),
        bar("MSFT", 0, 110.0),
    )


def overbought_bars(ticker: str, count: int = 60) -> tuple[OHLCVBar, ...]:
    """Return a long, steadily rising (overbought) series for one ticker.

    The technical engine treats a sustained climb as overbought (low RSI/Bollinger
    sub-scores), so the composite confidence lands below the regime floor — a
    deterministic rejection driven by indicators rather than the old scanner prior.
    """
    return tuple(
        bar(ticker, count - 1 - offset, 100.0 + offset) for offset in range(count)
    )


def candidate_set(*candidates: Candidate) -> CandidateSet:
    return CandidateSet(
        run_id="scanner-run-fixture",
        candidates=candidates,
        filter_trace=FilterTrace(
            universe_size=len(candidates), evaluated=len(candidates)
        ),
        explanation=Explanation(summary="fixture scan"),
        provenance=Provenance(
            run_id="scanner-run-fixture",
            source_agent="scanner",
            graph_node_id="ScanRun:scan-fixture",
        ),
    )


def candidate(ticker: str = "AAPL", score: float = 0.20) -> Candidate:
    return Candidate(
        ticker=ticker,
        rank=1,
        score=score,
        survived_filters=("min_price", "min_average_volume", "min_relative_strength"),
        metrics={"relative_strength": score},
    )


def recommendation(ticker: str = "AAPL") -> Recommendation:
    return Recommendation(
        ticker=ticker,
        action="buy",
        confidence=0.80,
        technical_score=0.75,
        rationale=Explanation(summary="fixture recommendation"),
    )


def analyze_message(payload: CandidateSet) -> AgentMessage:
    return AgentMessage(
        sender="tester",
        recipient="analyst",
        message_type="request",
        capability="analyze",
        payload=payload.model_dump(mode="json"),
    )


def explain_message(payload: CandidateSet) -> AgentMessage:
    return AgentMessage(
        sender="tester",
        recipient="analyst",
        message_type="request",
        capability="explain_recommendation",
        payload=payload.model_dump(mode="json"),
    )


def wire_analyst(
    *,
    source_bars: tuple[OHLCVBar, ...] = (),
    register_provider: bool = True,
    fail_ohlcv: bool = False,
    fail_regime: bool = False,
    settings: AnalystSettings | None = None,
) -> tuple[InProcessBus, InMemoryGraphStore, CollectingFaultSink]:
    bus = InProcessBus()
    graph = InMemoryGraphStore()
    sink = CollectingFaultSink()
    if register_provider:
        ProviderAgent(
            bus,
            graph=graph,
            source=FakeDataSource(
                bars=source_bars,
                vix=12.0,
                fail_ohlcv=fail_ohlcv,
                fail_regime=fail_regime,
            ),
            settings=ProviderSettings(max_staleness_days=7),
        ).bind()
    AnalystAgent(bus, graph=graph, settings=settings, sink=sink).bind()
    return bus, graph, sink
