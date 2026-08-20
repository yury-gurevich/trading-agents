"""Portfolio Manager graph-market correlation input tests.

Agent: portfolio_manager
Role: prove correlation uses run MarketData without widening provider calls.
External I/O: none.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from agents.portfolio_manager import PortfolioManagerAgent
from agents.portfolio_manager.settings import PortfolioManagerSettings
from agents.portfolio_manager.tests.helpers import (
    bar as recent_bar,
)
from agents.portfolio_manager.tests.helpers import (
    cash_portfolio,
    evaluate_message,
    recommendation_set,
)
from agents.portfolio_manager.tests.s184_helpers import (
    SECTORS,
    buy,
    correlated_bars,
)
from agents.provider import ProviderAgent
from agents.provider.settings import ProviderSettings
from agents.provider.sources import FakeDataSource
from contracts.common import Money, Provenance
from contracts.portfolio_manager import OrderIntentSet
from contracts.provider import (
    MARKET_DATA_LABEL,
    DataQualityTrace,
    MarketData,
    OHLCVBar,
)
from kernel import CollectingFaultSink, InMemoryGraphStore, InProcessBus

if TYPE_CHECKING:
    from contracts.common import Window


def test_correlation_uses_graph_market_data_without_widening_provider_call() -> None:
    """PM-NEV-08: correlation uses run MarketData, not a wider provider call."""
    bus = InProcessBus()
    graph = InMemoryGraphStore()
    source = RecordingSource(
        bars=(recent_bar("AMZN", 0, 100.0),),
        sectors={"AMZN": "Retail"},
        vix=12.0,
    )
    ProviderAgent(
        bus,
        graph=graph,
        source=source,
        settings=ProviderSettings(max_staleness_days=7),
    ).bind()
    PortfolioManagerAgent(
        bus,
        graph=graph,
        settings=PortfolioManagerSettings(
            starting_cash=Decimal("10000.00"),
            max_position_pct=Decimal("0.10"),
            max_positions=10,
            max_sector_pct=Decimal("0.50"),
            max_names_per_sector=3,
            max_correlated_cluster_pct=0.25,
        ),
        portfolio=cash_portfolio(
            "10000.00",
            {"AAPL": 10},
            position_values={"AAPL": Money(amount=Decimal("2000.00"))},
        ),
        issuer_map={},
        sink=CollectingFaultSink(),
    ).bind()
    recommendations = recommendation_set(buy("AMZN"))
    graph.merge_node(
        MARKET_DATA_LABEL,
        f"market-data:{recommendations.run_id}",
        {
            "snapshot": MarketData(
                bars=correlated_bars(("AAPL", "AMZN"), days=66),
                sectors=SECTORS,
                quality=DataQualityTrace(requested=2, returned=2),
                provenance=Provenance(
                    run_id=recommendations.run_id,
                    source_agent="provider",
                ),
            ).model_dump(mode="json")
        },
    )

    response = bus.request(evaluate_message(recommendations))
    orders = OrderIntentSet.model_validate(response.payload)

    assert response.message_type == "response"
    assert source.ohlcv_requests == (("AMZN",),)
    assert orders.approved == ()
    assert orders.rejected[0].reason == "correlated_cluster_concentration"


class RecordingSource(FakeDataSource):
    """Fake provider source that records OHLCV request shapes."""

    def __init__(
        self,
        *,
        bars: tuple[OHLCVBar, ...],
        sectors: dict[str, str],
        vix: float,
    ) -> None:
        super().__init__(bars=bars, sectors=sectors, vix=vix)
        self.ohlcv_requests: tuple[tuple[str, ...], ...] = ()

    def fetch_ohlcv(
        self, tickers: tuple[str, ...], window: Window
    ) -> tuple[OHLCVBar, ...]:
        self.ohlcv_requests = (*self.ohlcv_requests, tickers)
        return super().fetch_ohlcv(tickers, window)
