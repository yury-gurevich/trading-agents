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
from agents.scanner.domain.filter_attestation import evaluate_filters
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
    skipped_filters: tuple[str, ...]
    metrics: dict[str, float]


def apply_filters(
    tickers: tuple[str, ...],
    bars: tuple[OHLCVBar, ...],
    benchmark_bars: tuple[OHLCVBar, ...],
    earnings: dict[str, date],
    as_of: date,
    settings: ScannerSettings,
    earnings_horizon_days: int | None = None,
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
        fired, passed, skipped = evaluate_filters(
            features, settings, earnings_horizon_days
        )
        if fired is None:
            verdicts.append(
                FilterVerdict(
                    ticker=ticker,
                    decision="survived",
                    skipped_filters=skipped,
                    features=features,
                )
            )
            survivors.append(Survivor(ticker, passed, skipped, features))
        else:
            drops[fired] += 1
            verdicts.append(
                FilterVerdict(
                    ticker=ticker,
                    decision="dropped",
                    filter_fired=fired,
                    skipped_filters=skipped,
                    features=features,
                    bypassed=bypass,
                )
            )
            if bypass:
                survivors.append(Survivor(ticker, passed, skipped, features))
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


def _days_to_earnings(
    ticker: str, earnings: dict[str, date], as_of: date
) -> int | None:
    """Whole days until ``ticker``'s earnings; negative if known date is past."""
    next_date = earnings.get(ticker)
    if next_date is None:
        return None
    return (next_date - as_of).days


def _group_bars(bars: tuple[OHLCVBar, ...]) -> dict[str, tuple[OHLCVBar, ...]]:
    grouped: dict[str, list[OHLCVBar]] = {}
    for bar in bars:
        grouped.setdefault(bar.ticker, []).append(bar)
    return {ticker: tuple(rows) for ticker, rows in grouped.items()}
