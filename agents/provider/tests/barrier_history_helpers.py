"""Provider BarrierHistory test fixtures (S239 / DL-241 D10).

Agent: provider
Role: build smooth multi-year bars, a counting fake source, a provider, analyst runs
      with mixed recommendations, and read the written BarrierHistory back.
External I/O: none.
"""

from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING

from agents.provider import ProviderAgent
from agents.provider.settings import ProviderSettings
from agents.provider.sources import FakeDataSource
from contracts.analyst import Recommendation, RecommendationSet
from contracts.barrier_history import BarrierHistory
from contracts.common import Explanation, Provenance
from contracts.provider import OHLCVBar
from kernel import InProcessBus

if TYPE_CHECKING:
    from contracts.common import Window
    from kernel import GraphStore, Node

PACK = Path(__file__).resolve().parents[3] / "orchestration/packs"
TODAY = datetime.now(tz=UTC).date()


def bars(ticker: str, count: int, *, end_days_ago: int = 0) -> tuple[OHLCVBar, ...]:
    """Smooth daily bars ending ``end_days_ago`` days before today."""
    rows: list[OHLCVBar] = []
    close = 100.0
    for index in range(count):
        open_ = close
        close = open_ * math.exp(0.01 * math.sin(index * 1.37))
        rows.append(
            OHLCVBar(
                ticker=ticker,
                bar_date=TODAY - timedelta(days=end_days_ago + count - 1 - index),
                open=open_,
                high=max(open_, close) * 1.004,
                low=min(open_, close) * 0.996,
                close=close,
                volume=1_000_000,
            )
        )
    return tuple(rows)


class CountingSource(FakeDataSource):
    """A fake source that keeps every OHLCV request it served."""

    def __init__(self, bars: tuple[OHLCVBar, ...], *, fail: bool = False) -> None:
        super().__init__(bars=bars, fail_ohlcv=fail)
        self.asks: list[tuple[tuple[str, ...], Window]] = []

    def fetch_ohlcv(
        self, tickers: tuple[str, ...], window: Window
    ) -> tuple[OHLCVBar, ...]:
        self.asks.append((tickers, window))
        return super().fetch_ohlcv(tickers, window)


def counting_source(
    bars: tuple[OHLCVBar, ...], *, fail: bool = False
) -> CountingSource:
    return CountingSource(bars, fail=fail)


def provider_agent(graph: GraphStore, source: FakeDataSource) -> ProviderAgent:
    return ProviderAgent(
        InProcessBus(),
        graph=graph,
        source=source,
        settings=ProviderSettings(max_staleness_days=7),
    )


def rec(ticker: str, action: str, target: float | None = 0.07) -> Recommendation:
    return Recommendation.model_validate(
        {
            "ticker": ticker,
            "action": action,
            "confidence": 0.8,
            "technical_score": 0.7,
            "suggested_stop_pct": 0.05,
            "suggested_target_pct": target,
            "rationale": Explanation(summary=f"{ticker} fixture"),
        }
    )


def analyst_run(graph: GraphStore, *recs: Recommendation, key: str = "ar-1") -> Node:
    recommendation_set = RecommendationSet(
        run_id=key,
        recommendations=recs,
        rejections=(),
        explanation=Explanation(summary="fixture run"),
        provenance=Provenance(run_id=key, source_agent="analyst"),
    )
    return graph.merge_node(
        "AnalystRun",
        key,
        {"recommendation_set": recommendation_set.model_dump(mode="json")},
    )


def read_history(graph: GraphStore, key: str = "ar-1") -> BarrierHistory:
    node = graph.get_node("BarrierHistory", f"barrier-history:{key}")
    assert node is not None
    return BarrierHistory.model_validate(dict(node.props))


MIXED = (
    rec("AAPL", "buy"),
    rec("MSFT", "buy", target=None),
    rec("NVDA", "sell"),
    rec("AMZN", "hold"),
    rec("GOOG", "buy"),
)
