"""Market evidence renderers for the deliberator.

Agent: deliberator
Role: render provider market data with explicit unit/scope labels.
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from agents.deliberator.context_values import source_metric_map
from contracts.provider import REGIME_CONTEXT_LABEL, MarketData, OHLCVBar, RegimeContext

if TYPE_CHECKING:
    from kernel import GraphStore, Node


def market_lines(market: MarketData, ticker: str) -> list[str]:
    """Render provider evidence for one ticker."""
    lines = [
        "Market data quality: "
        f"requested_tickers={market.quality.requested}; "
        f"returned_tickers={market.quality.returned}; "
        f"used_fallback={market.quality.used_fallback}; "
        f"stale_tickers={list(market.quality.stale_tickers)}; "
        f"anomalous_tickers={list(market.quality.anomalous_tickers)}; "
        f"notes={list(market.quality.notes)}",
    ]
    bar = _latest_bar(market.bars, ticker)
    if bar is not None:
        lines.append(
            f"Latest OHLCV for {ticker}: date={bar.bar_date}; "
            f"open_usd={bar.open:.4g}; high_usd={bar.high:.4g}; "
            f"low_usd={bar.low:.4g}; close_usd={bar.close:.4g}; "
            f"volume_shares={bar.volume}"
        )
    if ticker in market.fundamentals:
        metrics = source_metric_map(market.fundamentals[ticker])
        lines.append(f"Fundamentals for {ticker}: {metrics}")
    if ticker in market.sentiment:
        lines.append(
            f"Provider sentiment for {ticker}: "
            f"provider_sentiment_score={market.sentiment[ticker]:.3f}"
        )
    if ticker in market.sectors:
        lines.append(f"Sector for {ticker}: {market.sectors[ticker]}")
    if ticker in market.earnings:
        lines.append(f"Next earnings for {ticker}: {market.earnings[ticker]}")
    if ticker in market.news:
        lines.append(f"News for {ticker}: {' | '.join(market.news[ticker])}")
    return lines


def regime_context(graph: GraphStore, market_node: Node) -> RegimeContext | None:
    """Resolve the RegimeContext linked to the market snapshot."""
    key = f"regime-context:{market_node.props['run_id']}"
    node = graph.get_node(REGIME_CONTEXT_LABEL, key)
    return RegimeContext.model_validate(node.props["snapshot"]) if node else None


def _latest_bar(items: tuple[OHLCVBar, ...], ticker: str) -> OHLCVBar | None:
    bars = [item for item in items if item.ticker == ticker]
    return max(bars, key=lambda item: item.bar_date) if bars else None
