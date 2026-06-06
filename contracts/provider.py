"""Provider agent contract — the single boundary to the outside market world.

Agent: provider
Role: contract — typed boundary (capabilities, owned data, never-do).
External I/O: market-data APIs (stooq, finnhub, fred, edgar, finbert).
"""

from __future__ import annotations

from datetime import date, datetime

from pydantic import Field

from contracts.common import (
    Provenance,
    RegimeLabel,
    Ticker,
    Window,
    _Frozen,
)
from kernel.contract import AgentContract, Capability


# ── Inbound payloads ────────────────────────────────────────────────────────
class DataRequest(_Frozen):
    tickers: tuple[Ticker, ...]
    window: Window
    fields: tuple[str, ...] = ("ohlcv",)
    """Subset of: ohlcv, fundamentals, news, earnings_calendar."""


class RegimeRequest(_Frozen):
    as_of: date


# ── Outbound payloads ───────────────────────────────────────────────────────
class OHLCVBar(_Frozen):
    ticker: Ticker
    bar_date: date
    open: float
    high: float
    low: float
    close: float
    volume: int


class DataQualityTrace(_Frozen):
    """Honest record of how clean this data is — degraded sources are first-class."""

    requested: int
    returned: int
    used_fallback: bool = False
    stale_tickers: tuple[Ticker, ...] = ()
    notes: tuple[str, ...] = ()


class MarketData(_Frozen):
    bars: tuple[OHLCVBar, ...]
    fundamentals: dict[Ticker, dict[str, float]] = Field(default_factory=dict)
    news: dict[Ticker, tuple[str, ...]] = Field(default_factory=dict)
    quality: DataQualityTrace
    provenance: Provenance


class RegimeContext(_Frozen):
    """Market regime + the policy inputs every downstream agent reads."""

    label: RegimeLabel
    vix: float | None
    as_of: datetime
    base_min_confidence: float
    base_stop_loss_pct: float
    base_take_profit_pct: float
    base_max_holding_days: int
    provenance: Provenance


CONTRACT = AgentContract(
    name="provider",
    version="0.1.0",
    mission=(
        "Be the single boundary to the outside market world. Turn raw external "
        "feeds into clean, validated, cached market facts and the current regime, "
        "so no other agent ever calls an external data API directly."
    ),
    consumes=(
        Capability(
            "get_market_data",
            "Fetch validated OHLCV/fundamentals/news for tickers over a window.",
            request=DataRequest,
            response=MarketData,
            mcp=True,
        ),
        Capability(
            "get_regime",
            "Classify the current market regime and emit policy inputs.",
            request=RegimeRequest,
            response=RegimeContext,
            mcp=True,
        ),
    ),
    emits=("market_data_degraded",),
    owns_graph=("MarketSnapshot", "Regime", "Ticker"),
    external_io=("stooq", "finnhub", "fred", "edgar", "finbert", "sp500_listing"),
    depends_on=(),
    mcp_tools=("get_market_data", "get_regime"),
    never=(
        "make trading decisions",
        "be imported by another agent (callers must send a request)",
        "expose raw provider credentials downstream",
    ),
)
