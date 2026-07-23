"""ADR-0015 graph-pull regression tests.

Agent: orchestration
Role: prove decision-time close lineage does not strand held names.
External I/O: none.
"""

from __future__ import annotations

from agents.analyst.settings import AnalystSettings
from agents.analyst.tests.helpers import overbought_bars
from agents.execution.broker import PaperBroker
from agents.provider import ProviderAgent
from agents.provider.settings import ProviderSettings
from kernel import InMemoryGraphStore, InProcessBus, Node
from orchestration.local_pipeline import cascade_once
from orchestration.start import place_run_request
from orchestration.tests.helpers import ReboundingDataSource, entry_bars, rebound_bars


def test_graph_pull_cascade_sells_previously_decided_close_holding() -> None:
    """ADR-0015 s1: a stranded close intent still reaches the sell rail."""
    graph = InMemoryGraphStore()
    broker = PaperBroker()
    held = _position(graph, "AMD", 7)
    close = graph.merge_node("CloseDecision", "held:AMD:close", {"decision": "close"})
    graph.add_edge(close, held, "CLOSES")
    source = ReboundingDataSource(
        entry=(*entry_bars(), *overbought_bars("AMD")),
        rebound=rebound_bars(),
    )
    agent = ProviderAgent(
        InProcessBus(),
        graph=graph,
        source=source,
        settings=ProviderSettings(max_staleness_days=7),
    )

    place_run_request(graph, run_id="unstrands-amd", tickers=("AAPL", "MSFT"))
    cascade_once(
        graph,
        provider_agent=agent,
        broker=broker,
        analyst_settings=AnalystSettings(exit_confidence_floor=0.58),
    )

    market = graph.get_node("MarketData", "market-data:unstrands-amd")
    assert market is not None
    assert "AMD" in market.props["tickers"]
    assert ("AMD", "sell", 7) in {
        (fill.ticker, fill.side, fill.quantity) for fill in broker.fills()
    }


def _position(graph: InMemoryGraphStore, ticker: str, quantity: int) -> Node:
    return graph.merge_node(
        "Position",
        f"held:{ticker}",
        {
            "run_id": "seed",
            "ticker": ticker,
            "quantity": quantity,
            "opened_price_cents": 10000,
            "stop_pct": 0.05,
            "target_pct": 0.10,
            "horizon_days": 10,
            "opened_at": "2026-07-20",
            "status": "open",
        },
    )
