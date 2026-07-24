"""Analyst batch-scoring pipeline.

Agent: analyst
Role: score a full CandidateSet against market data, regime, and benchmarks;
      group OHLCV bars by ticker for per-candidate lookups.
External I/O: none.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from typing import TYPE_CHECKING

from agents.analyst.domain.alpha_features import compute_alpha_features
from agents.analyst.domain.alpha_pillar import score_alpha158
from agents.analyst.domain.recommend import AnalysisDecision, decide
from agents.analyst.domain.scoring import score_candidate
from contracts.stop_rule import check_stop
from kernel.errors import fault_boundary, fault_from_exception

if TYPE_CHECKING:
    from agents.analyst.settings import AnalystSettings
    from contracts.positions import PositionStopThreshold
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
    held_tickers: tuple[str, ...] = (),
    held_stops: tuple[PositionStopThreshold, ...] = (),
) -> tuple[AnalysisDecision, ...] | None:
    """Score all candidates; returns None when the scoring step faults."""
    held = set(held_tickers)
    stop_thresholds = {threshold.ticker: threshold for threshold in held_stops}
    decisions: tuple[AnalysisDecision, ...] = ()
    with fault_boundary(
        sink,
        agent="analyst",
        module="agents.analyst.agent",
        capability="analyze",
        reraise=False,
    ) as capture:
        bars = _bars_by_ticker(market.bars)
        alpha_scores: dict[str, float] = {}
        if settings.alpha158_pillar_weight > 0.0:
            feature_rows = {
                ticker: compute_alpha_features(tuple(bars.get(ticker, ())))
                for ticker in {c.ticker for c in candidate_set.candidates}
            }
            universe = tuple(v for v in feature_rows.values() if v is not None)
            if universe:
                for ticker, row in feature_rows.items():
                    if row is not None:
                        alpha_scores[ticker] = score_alpha158(row, universe)
        scored: list[AnalysisDecision] = []
        for candidate in candidate_set.candidates:
            ticker_bars = bars.get(candidate.ticker, ())
            if not _scorable(candidate.ticker, bars, held, sink):
                continue
            scored.append(
                decide(
                    candidate,
                    score_candidate(
                        candidate,
                        ticker_bars,
                        market.fundamentals.get(candidate.ticker, {}),
                        benchmark_bars,
                        market.news.get(candidate.ticker, ()),
                        settings,
                        alpha_score=alpha_scores.get(candidate.ticker),
                    ),
                    regime,
                    held=candidate.ticker in held,
                    exit_confidence_floor=settings.exit_confidence_floor,
                    stop_breached=_stop_breached(
                        candidate.ticker, ticker_bars, stop_thresholds
                    ),
                )
            )
        decisions = tuple(scored)
    return None if capture.fault is not None else decisions


def _bars_by_ticker(bars: tuple[OHLCVBar, ...]) -> dict[str, tuple[OHLCVBar, ...]]:
    grouped: dict[str, list[OHLCVBar]] = {}
    for bar in bars:
        grouped.setdefault(bar.ticker, []).append(bar)
    return {ticker: tuple(rows) for ticker, rows in grouped.items()}


def _scorable(
    ticker: str, bars: dict[str, tuple[OHLCVBar, ...]], held: set[str], sink: FaultSink
) -> bool:
    if ticker not in held or bars.get(ticker):
        return True
    sink.submit(
        fault_from_exception(
            RuntimeError(f"held ticker {ticker} has no market data"),
            agent="analyst",
            module="agents.analyst.domain.analyze",
            capability="analyze",
        )
    )
    return False


def _stop_breached(
    ticker: str,
    bars: tuple[OHLCVBar, ...],
    thresholds: dict[str, PositionStopThreshold],
) -> bool:
    threshold = thresholds.get(ticker)
    if threshold is None or not bars:
        return False
    return check_stop(
        _latest_close_cents(bars),
        threshold.opened_price_cents,
        threshold.stop_pct,
    )


def _latest_close_cents(bars: tuple[OHLCVBar, ...]) -> int:
    close = max(bars, key=lambda bar: bar.bar_date).close
    return int(
        (Decimal(str(close)) * Decimal("100")).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP
        )
    )
