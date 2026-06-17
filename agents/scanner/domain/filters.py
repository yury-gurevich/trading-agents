"""Scanner filter chain.

Agent: scanner
Role: reduce market data to surviving ticker metrics with attributable drops.
External I/O: none.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import TYPE_CHECKING

from agents.scanner.domain.beta import compute_beta
from contracts.scanner import FilterTrace

if TYPE_CHECKING:
    from agents.scanner.settings import ScannerSettings
    from contracts.provider import OHLCVBar


@dataclass(frozen=True)
class Survivor:
    """Ticker that passed the scanner filters."""

    ticker: str
    survived_filters: tuple[str, ...]
    metrics: dict[str, float]


def apply_filters(
    tickers: tuple[str, ...],
    bars: tuple[OHLCVBar, ...],
    benchmark_bars: tuple[OHLCVBar, ...],
    settings: ScannerSettings,
) -> tuple[tuple[Survivor, ...], FilterTrace]:
    """Apply the scanner's deterministic filter chain (price, liquidity, RS, beta)."""
    grouped = _group_bars(bars)
    drops: Counter[str] = Counter()
    survivors: list[Survivor] = []
    for ticker in tickers:
        ticker_bars = sorted(grouped.get(ticker, ()), key=lambda bar: bar.bar_date)
        if len(ticker_bars) < 2:
            drops["missing_history"] += 1
            continue
        latest = ticker_bars[-1]
        avg_volume = sum(bar.volume for bar in ticker_bars) / len(ticker_bars)
        total_return = (latest.close - ticker_bars[0].close) / ticker_bars[0].close
        if latest.close < settings.min_price:
            drops["min_price"] += 1
            continue
        if avg_volume < settings.min_average_volume:
            drops["min_average_volume"] += 1
            continue
        if total_return < settings.min_relative_strength:
            drops["min_relative_strength"] += 1
            continue
        beta = compute_beta(
            tuple(ticker_bars), benchmark_bars, settings.beta_min_observations
        )
        if beta is not None and beta > settings.max_beta:
            drops["max_beta"] += 1
            continue
        survivors.append(
            _survivor(ticker, latest.close, avg_volume, total_return, beta)
        )
    trace = FilterTrace(
        universe_size=len(tickers),
        evaluated=len(tickers),
        dropped_by_filter=dict(drops),
    )
    return tuple(survivors), trace


def _survivor(
    ticker: str,
    latest_close: float,
    avg_volume: float,
    total_return: float,
    beta: float | None,
) -> Survivor:
    """Build a survivor, recording beta + its gate only when beta was computable."""
    survived = ["min_price", "min_average_volume", "min_relative_strength"]
    metrics = {
        "latest_close": latest_close,
        "average_volume": avg_volume,
        "relative_strength": total_return,
    }
    if beta is not None:
        metrics["beta"] = beta
        survived.append("max_beta")
    return Survivor(ticker=ticker, survived_filters=tuple(survived), metrics=metrics)


def _group_bars(bars: tuple[OHLCVBar, ...]) -> dict[str, tuple[OHLCVBar, ...]]:
    grouped: dict[str, list[OHLCVBar]] = {}
    for bar in bars:
        grouped.setdefault(bar.ticker, []).append(bar)
    return {ticker: tuple(rows) for ticker, rows in grouped.items()}
