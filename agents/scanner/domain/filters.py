"""Scanner filter chain.

Agent: scanner
Role: reduce market data to surviving ticker metrics with attributable drops, and
      record a per-ticker verdict (decision + features) for filter-quality training.
External I/O: none.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import TYPE_CHECKING

from agents.scanner.domain.beta import compute_beta
from contracts.scanner import FilterTrace, FilterVerdict

if TYPE_CHECKING:
    from datetime import date

    from agents.scanner.settings import ScannerSettings
    from contracts.provider import OHLCVBar


@dataclass(frozen=True)
class Survivor:
    """Ticker that passed the scanner filters (or was bypassed through them)."""

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
    """Apply the filter chain; emit survivors, drop counts, and per-ticker verdicts."""
    grouped = _group_bars(bars)
    drops: Counter[str] = Counter()
    survivors: list[Survivor] = []
    verdicts: list[FilterVerdict] = []
    bypass = settings.bypass_scanner_filter
    for ticker in tickers:
        ticker_bars = sorted(grouped.get(ticker, ()), key=lambda bar: bar.bar_date)
        if len(ticker_bars) < 2:
            drops["missing_history"] += 1
            verdicts.append(
                FilterVerdict(
                    ticker=ticker, decision="dropped", filter_fired="missing_history"
                )
            )
            continue  # no bars to compute features from — bypass cannot rescue it
        features = _features(ticker_bars, benchmark_bars, earnings, as_of, settings)
        fired, passed = _evaluate(features, settings)
        if fired is None:
            verdicts.append(
                FilterVerdict(ticker=ticker, decision="survived", features=features)
            )
            survivors.append(Survivor(ticker, passed, features))
        else:
            drops[fired] += 1
            verdicts.append(
                FilterVerdict(
                    ticker=ticker,
                    decision="dropped",
                    filter_fired=fired,
                    features=features,
                    bypassed=bypass,
                )
            )
            if bypass:
                survivors.append(Survivor(ticker, passed, features))
    trace = FilterTrace(
        universe_size=len(tickers),
        evaluated=len(tickers),
        dropped_by_filter=dict(drops),
        verdicts=tuple(verdicts),
    )
    return tuple(survivors), trace


def _features(
    ticker_bars: list[OHLCVBar],
    benchmark_bars: tuple[OHLCVBar, ...],
    earnings: dict[str, date],
    as_of: date,
    settings: ScannerSettings,
) -> dict[str, float]:
    """Compute the features the filters judge a ticker on."""
    latest = ticker_bars[-1]
    avg_volume = sum(bar.volume for bar in ticker_bars) / len(ticker_bars)
    total_return = (latest.close - ticker_bars[0].close) / ticker_bars[0].close
    features = {
        "latest_close": latest.close,
        "average_volume": avg_volume,
        "relative_strength": total_return,
    }
    beta = compute_beta(
        tuple(ticker_bars), benchmark_bars, settings.beta_min_observations
    )
    if beta is not None:
        features["beta"] = beta
    days = _days_to_earnings(ticker_bars[0].ticker, earnings, as_of)
    if days is not None:
        features["days_to_earnings"] = float(days)
    return features


def _evaluate(
    features: dict[str, float], settings: ScannerSettings
) -> tuple[str | None, tuple[str, ...]]:
    """Return (first filter that drops the ticker | None, gates it passed in order)."""
    passed: list[str] = []
    if features["latest_close"] < settings.min_price:
        return "min_price", tuple(passed)
    passed.append("min_price")
    if features["average_volume"] < settings.min_average_volume:
        return "min_average_volume", tuple(passed)
    passed.append("min_average_volume")
    if features["relative_strength"] < settings.min_relative_strength:
        return "min_relative_strength", tuple(passed)
    passed.append("min_relative_strength")
    if "beta" in features:
        if features["beta"] > settings.max_beta:
            return "max_beta", tuple(passed)
        passed.append("max_beta")
    if "days_to_earnings" in features:
        if features["days_to_earnings"] <= settings.earnings_exclusion_days:
            return "earnings_window", tuple(passed)
        passed.append("earnings_window")
    return None, tuple(passed)


def _days_to_earnings(
    ticker: str, earnings: dict[str, date], as_of: date
) -> int | None:
    """Whole days until ``ticker``'s next earnings; None if unknown or already past."""
    next_date = earnings.get(ticker)
    if next_date is None:
        return None
    days = (next_date - as_of).days
    return days if days >= 0 else None


def _group_bars(bars: tuple[OHLCVBar, ...]) -> dict[str, tuple[OHLCVBar, ...]]:
    grouped: dict[str, list[OHLCVBar]] = {}
    for bar in bars:
        grouped.setdefault(bar.ticker, []).append(bar)
    return {ticker: tuple(rows) for ticker, rows in grouped.items()}
