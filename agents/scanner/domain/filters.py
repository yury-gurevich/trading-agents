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
    from datetime import date

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
    earnings: dict[str, date],
    as_of: date,
    settings: ScannerSettings,
) -> tuple[tuple[Survivor, ...], FilterTrace]:
    """Apply the scanner filter chain (price, liquidity, RS, beta, earnings window)."""
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
        days_to_earnings = _days_to_earnings(ticker, earnings, as_of)
        if (
            days_to_earnings is not None
            and days_to_earnings <= settings.earnings_exclusion_days
        ):
            drops["earnings_window"] += 1
            continue
        survivors.append(
            _survivor(
                ticker, latest.close, avg_volume, total_return, beta, days_to_earnings
            )
        )
    trace = FilterTrace(
        universe_size=len(tickers),
        evaluated=len(tickers),
        dropped_by_filter=dict(drops),
    )
    return tuple(survivors), trace


def _days_to_earnings(
    ticker: str, earnings: dict[str, date], as_of: date
) -> int | None:
    """Whole days until ``ticker``'s next earnings; None if unknown or already past."""
    next_date = earnings.get(ticker)
    if next_date is None:
        return None
    days = (next_date - as_of).days
    return days if days >= 0 else None


def _survivor(
    ticker: str,
    latest_close: float,
    avg_volume: float,
    total_return: float,
    beta: float | None,
    days_to_earnings: int | None,
) -> Survivor:
    """Build a survivor, recording the beta and earnings gates only when applied."""
    survived = ["min_price", "min_average_volume", "min_relative_strength"]
    metrics = {
        "latest_close": latest_close,
        "average_volume": avg_volume,
        "relative_strength": total_return,
    }
    if beta is not None:
        metrics["beta"] = beta
        survived.append("max_beta")
    if days_to_earnings is not None:
        metrics["days_to_earnings"] = float(days_to_earnings)
        survived.append("earnings_window")
    return Survivor(ticker=ticker, survived_filters=tuple(survived), metrics=metrics)


def _group_bars(bars: tuple[OHLCVBar, ...]) -> dict[str, tuple[OHLCVBar, ...]]:
    grouped: dict[str, list[OHLCVBar]] = {}
    for bar in bars:
        grouped.setdefault(bar.ticker, []).append(bar)
    return {ticker: tuple(rows) for ticker, rows in grouped.items()}
