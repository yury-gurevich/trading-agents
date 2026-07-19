"""Provider payload fixtures for deliberation veto context tests.

Agent: orchestration
Role: build MarketData and RegimeContext payloads used by veto context fixtures.
External I/O: none.
"""

from __future__ import annotations

from datetime import UTC, date, datetime

from contracts.common import Provenance
from contracts.provider import DataQualityTrace, MarketData, OHLCVBar, RegimeContext


def market_data(full: bool) -> dict[str, object]:
    """Return provider payload; sparse mode makes AAPL market facts absent."""
    ticker = "AAPL" if full else "MSFT"
    market = MarketData(
        bars=(
            OHLCVBar(
                ticker=ticker,
                bar_date=date(2026, 7, 2),
                open=110.0,
                high=115.0,
                low=109.0,
                close=114.0,
                volume=1_300_000,
            ),
            OHLCVBar(
                ticker=ticker,
                bar_date=date(2026, 7, 3),
                open=114.0,
                high=118.0,
                low=113.0,
                close=116.0,
                volume=1_500_000,
            ),
        ),
        fundamentals={"AAPL": {"pe": 28.5, "roe": 0.21}} if full else {},
        news={"AAPL": ("raises guidance", "buyback expanded")} if full else {},
        sentiment={"AAPL": 0.73} if full else {},
        sectors={"AAPL": "Technology"} if full else {},
        earnings={"AAPL": date(2026, 7, 30)} if full else {},
        quality=DataQualityTrace(
            requested=2,
            returned=1,
            used_fallback=not full,
            stale_tickers=("MSFT",) if full else (),
            anomalous_tickers=(),
            notes=("fixture",),
        ),
        provenance=prov("provider"),
    )
    return market.model_dump(mode="json")


def regime() -> dict[str, object]:
    """Return one regime context payload."""
    return RegimeContext(
        label="neutral",
        vix=14.2,
        as_of=datetime(2026, 7, 3, tzinfo=UTC),
        base_min_confidence=0.57,
        base_stop_loss_pct=0.03,
        base_take_profit_pct=0.08,
        base_max_holding_days=5,
        provenance=prov("provider"),
    ).model_dump(mode="json")


def prov(agent: str) -> Provenance:
    """Return minimal provenance for one source agent."""
    return Provenance(run_id=agent, source_agent=agent)
