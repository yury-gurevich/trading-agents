"""Provider optional market-data field gating.

Agent: provider
Role: fetch each optionally-requested MarketData field behind its own fault boundary,
      degrading to empty with an honest quality note instead of failing the request.
External I/O: none directly (delegates to the injected DataSource).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from kernel.errors import fault_boundary

if TYPE_CHECKING:
    from collections.abc import Callable
    from datetime import date

    from agents.provider.sources import DataSource
    from contracts.common import Window
    from contracts.provider import DataQualityTrace, OHLCVBar
    from kernel import FaultSink


@dataclass(frozen=True)
class OptionalFields:
    """The optional MarketData fields plus the (possibly degraded) quality trace."""

    fundamentals: dict[str, dict[str, float]]
    news: dict[str, tuple[str, ...]]
    sentiment: dict[str, float]
    sectors: dict[str, str]
    earnings: dict[str, date]
    benchmark: tuple[OHLCVBar, ...]
    quality: DataQualityTrace


def collect_optional_fields(
    source: DataSource,
    *,
    fields: tuple[str, ...],
    tickers: tuple[str, ...],
    window: Window,
    sink: FaultSink,
    quality: DataQualityTrace,
    benchmark_ticker: str | None = None,
) -> OptionalFields:
    """Fetch every requested optional field; skip unrequested, degrade on fault."""
    empty_funda: dict[str, dict[str, float]] = {}
    empty_news: dict[str, tuple[str, ...]] = {}
    empty_floats: dict[str, float] = {}
    empty_strs: dict[str, str] = {}
    empty_dates: dict[str, date] = {}
    empty_bars: tuple[OHLCVBar, ...] = ()
    fundamentals, quality = _fetch_optional(
        sink,
        requested="fundamentals" in fields,
        fetch=lambda: source.fetch_fundamentals(tickers, window),
        empty=empty_funda,
        note="fundamentals_degraded",
        quality=quality,
    )
    news, quality = _fetch_optional(
        sink,
        requested="news" in fields,
        fetch=lambda: source.fetch_news(tickers, window),
        empty=empty_news,
        note="news_degraded",
        quality=quality,
    )
    sentiment, quality = _fetch_optional(
        sink,
        requested="sentiment" in fields,
        fetch=lambda: source.fetch_sentiment(tickers),
        empty=empty_floats,
        note="sentiment_degraded",
        quality=quality,
    )
    sectors, quality = _fetch_optional(
        sink,
        requested="sectors" in fields,
        fetch=lambda: source.fetch_sectors(tickers),
        empty=empty_strs,
        note="sectors_degraded",
        quality=quality,
    )
    earnings, quality = _fetch_optional(
        sink,
        requested="earnings_calendar" in fields,
        fetch=lambda: source.fetch_earnings(tickers, window),
        empty=empty_dates,
        note="earnings_degraded",
        quality=quality,
    )
    benchmark = empty_bars
    if "benchmark" in fields and benchmark_ticker is not None:
        bench = benchmark_ticker
        benchmark, quality = _fetch_optional(
            sink,
            requested=True,
            fetch=lambda: source.fetch_ohlcv((bench,), window),
            empty=empty_bars,
            note="benchmark_degraded",
            quality=quality,
        )
    return OptionalFields(
        fundamentals=fundamentals,
        news=news,
        sentiment=sentiment,
        sectors=sectors,
        earnings=earnings,
        benchmark=benchmark,
        quality=quality,
    )


def _fetch_optional[T](
    sink: FaultSink,
    *,
    requested: bool,
    fetch: Callable[[], T],
    empty: T,
    note: str,
    quality: DataQualityTrace,
) -> tuple[T, DataQualityTrace]:
    """Fetch one optional field behind its own fault boundary.

    Returns the fetched value with unchanged quality on success; the empty value plus a
    NOTE on fault; the empty value with unchanged quality when not requested. An
    optional-field fault **never sets ``used_fallback`` (DRIFT-012):** a degraded
    fundamentals/news/sentiment/sectors/earnings/benchmark field forgoes *that* signal,
    never the whole analysis — only core OHLCV degradation (`validate_bars`) blocks
    trading. The fault is still routed to the central channel.
    """
    if not requested:
        return empty, quality
    value = empty
    with fault_boundary(
        sink,
        agent="provider",
        module="agents.provider.market_fields",
        capability="get_market_data",
        reraise=False,
    ) as capture:
        value = fetch()
    if capture.fault is not None:
        notes = (*quality.notes, note)
        return empty, quality.model_copy(update={"notes": notes})
    return value, quality
