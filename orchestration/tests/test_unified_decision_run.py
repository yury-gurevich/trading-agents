"""Unified buy/sell graph-pull cascade tests.

Agent: orchestration
Role: prove held tickers share the scanner-survivor evidence path into PM/execution.
External I/O: none.
"""

from __future__ import annotations

from agents.analyst.settings import AnalystSettings
from agents.analyst.tests.helpers import overbought_bars
from agents.execution.broker import PaperBroker
from agents.provider import ProviderAgent
from agents.provider.settings import ProviderSettings
from contracts.portfolio_manager import OrderIntentSet
from kernel import InMemoryGraphStore, InProcessBus
from orchestration.local_pipeline import cascade_once
from orchestration.start import place_run_request
from orchestration.tests.helpers import ReboundingDataSource, entry_bars, rebound_bars


def test_graph_pull_cascade_sells_held_low_confidence_name() -> None:
    """ADR-0016: graph-pull scores held+survivors and sends sell via OrderIntent."""
    graph = InMemoryGraphStore()
    broker = PaperBroker()
    _position(graph, "LOW", 7)
    source = ReboundingDataSource(
        entry=(*entry_bars(), *overbought_bars("LOW")),
        rebound=rebound_bars(),
    )
    agent = _provider(graph, source)

    place_run_request(graph, run_id="unified-sell", tickers=("AAPL", "MSFT"))
    cascade_once(
        graph,
        provider_agent=agent,
        broker=broker,
        analyst_settings=AnalystSettings(exit_confidence_floor=0.58),
    )

    market = graph.get_node("MarketData", "market-data:unified-sell")
    assert market is not None
    assert "LOW" in market.props["tickers"]
    fills = broker.fills()
    assert ("LOW", "sell", 7) in {
        (fill.ticker, fill.side, fill.quantity) for fill in fills
    }
    assert any(fill.side == "buy" and fill.ticker == "AAPL" for fill in fills)


def test_graph_pull_sell_replays_until_position_nodes_change() -> None:
    """ADR-0015/0016: unchanged exit holding reuses one broker idempotency key."""
    graph = InMemoryGraphStore()
    broker = PaperBroker(reject_tickers={"LOW"})
    _position(graph, "LOW", 7)
    source = ReboundingDataSource(
        entry=(*entry_bars(), *overbought_bars("LOW")),
        rebound=rebound_bars(),
        rebound_after_calls=99,
    )
    agent = _provider(graph, source)

    _run_sell(graph, agent, broker, "exit-1")
    _run_sell(graph, agent, broker, "exit-2")

    assert broker.order_count == 1
    assert [(fill.ticker, fill.side, fill.quantity) for fill in broker.fills()] == [
        ("LOW", "sell", 7)
    ]
    first_key = broker.fills()[0].idempotency_key

    graph.merge_node("Position", "held:LOW", {"broker_superseded_by": "remaining"})
    _position(graph, "LOW", 4, key="remaining:LOW")
    _run_sell(graph, agent, broker, "exit-3")

    keys = {fill.idempotency_key for fill in broker.fills()}
    assert broker.order_count == 2
    assert first_key in keys
    assert len(keys) == 2


def test_graph_pull_sets_position_ref_on_exits_only() -> None:
    """ADR-0016: PM emits entry and exit intents on one graph-pull rail."""
    graph = InMemoryGraphStore()
    broker = PaperBroker()
    _position(graph, "LOW", 7)
    source = ReboundingDataSource(
        entry=(*entry_bars(), *overbought_bars("LOW")),
        rebound=rebound_bars(),
    )
    agent = _provider(graph, source)

    place_run_request(graph, run_id="entry-and-exit", tickers=("AAPL", "MSFT"))
    cascade_once(
        graph,
        provider_agent=agent,
        broker=broker,
        analyst_settings=AnalystSettings(exit_confidence_floor=0.58),
    )

    intents = _latest_order_set(graph).approved
    by_ticker = {intent.ticker: intent for intent in intents}
    assert by_ticker["AAPL"].action == "buy"
    assert by_ticker["AAPL"].position_ref is None
    assert by_ticker["LOW"].action == "sell"
    assert by_ticker["LOW"].position_ref is not None


def test_graph_pull_held_survivor_holds_without_pyramiding() -> None:
    """ADR-0016: held survivor above exit floor is hold, never a duplicate buy."""
    graph = InMemoryGraphStore()
    broker = PaperBroker()
    _position(graph, "AAPL", 3)
    source = ReboundingDataSource(entry=entry_bars(), rebound=rebound_bars())
    agent = _provider(graph, source)

    place_run_request(graph, run_id="unified-hold", tickers=("AAPL",))
    cascade_once(graph, provider_agent=agent, broker=broker)

    recommendations = graph.list_nodes("Recommendation")
    assert [(r.props["ticker"], r.props["action"]) for r in recommendations] == [
        ("AAPL", "hold")
    ]
    assert broker.fills() == ()
    assert graph.list_nodes("OrderIntent") == ()


def _provider(graph: InMemoryGraphStore, source: ReboundingDataSource) -> ProviderAgent:
    return ProviderAgent(
        InProcessBus(),
        graph=graph,
        source=source,
        settings=ProviderSettings(max_staleness_days=7),
    )


def _run_sell(
    graph: InMemoryGraphStore,
    agent: ProviderAgent,
    broker: PaperBroker,
    run_id: str,
) -> None:
    place_run_request(graph, run_id=run_id, tickers=("LOW",))
    cascade_once(
        graph,
        provider_agent=agent,
        broker=broker,
        analyst_settings=AnalystSettings(exit_confidence_floor=0.58),
    )


def _latest_order_set(graph: InMemoryGraphStore) -> OrderIntentSet:
    node = graph.list_nodes("PMRun")[-1]
    return OrderIntentSet.model_validate(node.props["order_intent_set"])


def _position(
    graph: InMemoryGraphStore, ticker: str, quantity: int, *, key: str | None = None
) -> None:
    graph.merge_node(
        "Position",
        key or f"held:{ticker}",
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
