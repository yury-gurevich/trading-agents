"""Provider optional market-data field gating.

Agent: provider
Role: fetch optional fields behind independent fault boundaries.
External I/O: delegates to the injected DataSource.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import partial
from typing import TYPE_CHECKING

from contracts.feed_notes import consume_degraded_feed_notes
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
    """The optional MarketData fields plus the quality trace."""

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
    fetch_optional = partial(_fetch_optional, sink, source=source)
    fundamentals, quality = fetch_optional(
        requested="fundamentals" in fields,
        fetch=lambda: source.fetch_fundamentals(tickers, window),
        empty=empty_funda,
        note="fundamentals_degraded",
        quality=quality,
    )
    news, quality = fetch_optional(
        requested="news" in fields,
        fetch=lambda: source.fetch_news(tickers, window),
        empty=empty_news,
        note="news_degraded",
        quality=quality,
    )
    sentiment, quality = fetch_optional(
        requested="sentiment" in fields,
        fetch=lambda: source.fetch_sentiment(tickers),
        empty=empty_floats,
        note="sentiment_degraded",
        quality=quality,
    )
    sectors, quality = fetch_optional(
        requested="sectors" in fields,
        fetch=lambda: source.fetch_sectors(tickers),
        empty=empty_strs,
        note="sectors_degraded",
        quality=quality,
    )
    earnings, quality = fetch_optional(
        requested="earnings_calendar" in fields,
        fetch=lambda: source.fetch_earnings(tickers, window),
        empty=empty_dates,
        note="earnings_degraded",
        quality=quality,
    )
    benchmark = empty_bars
    if "benchmark" in fields and benchmark_ticker is not None:
        bench = benchmark_ticker
        benchmark, quality = fetch_optional(
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
    source: object,
) -> tuple[T, DataQualityTrace]:
    """Fetch one optional field; enrichment faults never taint OHLCV (DRIFT-012)."""
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
    notes = consume_degraded_feed_notes(source)
    if notes:
        quality = quality.model_copy(
            update={"notes": tuple(dict.fromkeys((*quality.notes, *notes)))}
        )
    return value, quality
