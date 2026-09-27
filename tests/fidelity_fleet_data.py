"""Synthetic market inputs for the S237 fleet-produced fidelity fixtures.

Agent: tooling
Role: deterministic bars, benchmark, sectors, fundamentals, news and earnings dates.
External I/O: none.
"""

from __future__ import annotations

import math
from datetime import UTC, date, datetime, timedelta

from scripts.replay_settings import build_effective_settings

from contracts.common import Provenance
from contracts.provider import DataQualityTrace, MarketData, OHLCVBar, RegimeContext
from orchestration.history_window import declared_lookback_days

LAST_SESSION = date(2026, 10, 2)
SESSIONS = (
    date(2026, 9, 28),
    date(2026, 9, 29),
    date(2026, 9, 30),
    date(2026, 10, 1),
    LAST_SESSION,
)
TICKERS = tuple(f"T{index:02d}" for index in range(32))
HELD_ONLY = "Z99"  # held, outside the scanner's universe: scoring_universe adds it
HIGH_BETA = "T31"  # moves three times SPY: the beta cap drops it when SPY is stored
SECTOR_NAMES = ("Tech", "Health", "Energy", "Banks")
IEX_SHARE = 0.03  # the snapshot's volume as a slice of the cache's (DL-233: 2-5 %)
EARNINGS_HORIZON_DAYS = 14


def business_days(end: date, count: int) -> tuple[date, ...]:
    """Return the last ``count`` weekdays ending at ``end``."""
    days: list[date] = []
    day = end
    while len(days) < count:
        if day.weekday() < 5:
            days.append(day)
        day -= timedelta(days=1)
    return tuple(reversed(days))


CALENDAR = business_days(LAST_SESSION, 280)
_SETTINGS = build_effective_settings(())


def window_days(session: date) -> tuple[date, ...]:
    """Return the sessions a run ships: the declared history window (Trap 4)."""
    days = declared_lookback_days(
        _SETTINGS.analyst,
        as_of=session,
        staleness_buffer_sessions=_SETTINGS.provider.max_staleness_days,
    )
    start = session - timedelta(days=days)
    return tuple(day for day in CALENDAR if start <= day <= session)


def ticker_index(ticker: str) -> int:
    """Return the synthetic series index of a ticker."""
    return 40 if ticker == HELD_ONLY else int(ticker[1:])


def sector(ticker: str) -> str:
    """Return the fixture sector label; the held names share Banks."""
    return "Banks" if ticker == HELD_ONLY else SECTOR_NAMES[ticker_index(ticker) % 4]


def close(ticker: str, day: date) -> float:
    """Return one deterministic close; every fifth name trends down."""
    index = ticker_index(ticker)
    step = CALENDAR.index(day)
    if ticker == HIGH_BETA:
        return round(60 * math.exp(0.0015 * step) * (1 + 0.03 * math.sin(step / 9)), 4)
    drift = -0.0008 if index % 5 == 0 else 0.0006 + 0.0001 * (index % 7)
    wave = (0.02 + 0.004 * (index % 4)) * math.sin(step / (5 + index % 7))
    return round((20 + 3 * index) * math.exp(drift * step) * (1 + wave), 4)


def sip_volume(ticker: str, day: date) -> int:
    """Return the consolidated (SIP) volume the cache holds for one bar."""
    return 900_000 + 10_000 * ticker_index(ticker) + 1_000 * (CALENDAR.index(day) % 9)


def ticker_bars(
    ticker: str, session: date, *, volume_share: float = 1.0
) -> tuple[OHLCVBar, ...]:
    """Return the bars a run on ``session`` would ship for a ticker."""
    rows: list[OHLCVBar] = []
    for day in window_days(session):
        price = close(ticker, day)
        rows.append(
            OHLCVBar(
                ticker=ticker,
                bar_date=day,
                open=round(price * 0.995, 4),
                high=round(price * 1.01, 4),
                low=round(price * 0.99, 4),
                close=price,
                volume=int(sip_volume(ticker, day) * volume_share),
            )
        )
    return tuple(rows)


def spy_bar(day: date) -> OHLCVBar:
    """Return one SPY bar."""
    return OHLCVBar(
        ticker="SPY",
        bar_date=day,
        open=400.0,
        high=404.0,
        low=396.0,
        close=round(400 * (1 + 0.01 * math.sin(CALENDAR.index(day) / 9)), 4),
        volume=50_000_000,
    )


def benchmark_bars(session: date) -> tuple[OHLCVBar, ...]:
    """Return SPY bars over the session's window."""
    return tuple(spy_bar(day) for day in window_days(session))


def market_data(
    run_id: str,
    session: date,
    universe: tuple[str, ...],
    *,
    benchmark: bool = True,
    enriched: bool = True,
    volume_share: float = 1.0,
) -> MarketData:
    """Return the provider snapshot a scheduled run would store."""
    bars = tuple(
        bar
        for ticker in universe
        for bar in ticker_bars(ticker, session, volume_share=volume_share)
    )
    return MarketData(
        bars=bars,
        benchmark=benchmark_bars(session) if benchmark else (),
        fundamentals=_fundamentals(universe) if enriched else {},
        news=_news(universe) if enriched else {},
        sectors={ticker: sector(ticker) for ticker in universe},
        earnings=_earnings(session) if enriched else {},
        earnings_horizon_days=EARNINGS_HORIZON_DAYS if enriched else None,
        quality=DataQualityTrace(requested=len(universe), returned=len(universe)),
        provenance=Provenance(run_id=run_id, source_agent="provider"),
    )


def regime(run_id: str, session: date) -> RegimeContext:
    """Return the run's stored regime; its floor rejects the weakest candidates."""
    return RegimeContext(
        label="neutral",
        vix=18.0,
        vix_status="measured",
        vix_as_of=session,
        as_of=datetime.combine(session, datetime.min.time(), tzinfo=UTC),
        base_min_confidence=0.55,
        base_stop_loss_pct=0.05,
        base_take_profit_pct=0.10,
        base_max_holding_days=10,
        provenance=Provenance(run_id=run_id, source_agent="provider"),
    )


def _fundamentals(universe: tuple[str, ...]) -> dict[str, dict[str, float]]:
    return {
        ticker: {
            "peTTM": 12.0 + ticker_index(ticker) % 20,
            "roeTTM": 8.0 + ticker_index(ticker) % 15,
            "netProfitMarginTTM": 6.0 + ticker_index(ticker) % 18,
            "currentRatioQuarterly": 1.2,
        }
        for ticker in universe
        if ticker_index(ticker) % 3 == 0
    }


def _news(universe: tuple[str, ...]) -> dict[str, tuple[str, ...]]:
    good = ("record profit growth beats estimates", "strong demand lifts outlook")
    bad = ("lawsuit probe weighs on shares", "weak guidance disappoints")
    return {
        ticker: good if ticker_index(ticker) % 2 else bad
        for ticker in universe
        if ticker_index(ticker) % 4 in (1, 2)
    }


def _earnings(session: date) -> dict[str, date]:
    return {"T08": session + timedelta(days=2), "T13": session + timedelta(days=30)}
