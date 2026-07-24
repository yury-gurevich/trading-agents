"""Realized-PnL graph-pull regression tests.

Agent: orchestration
Role: prove execution poll reconciliation appends fill-time realized PnL.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

from agents.execution.broker import BrokerFill, BrokerPosition
from agents.provider import ProviderAgent
from agents.provider.settings import ProviderSettings
from contracts.common import Explanation, Money, Provenance
from contracts.portfolio_manager import OrderIntentSet
from contracts.positions import open_positions
from kernel import InMemoryGraphStore, InProcessBus
from orchestration.local_pipeline import cascade_once
from orchestration.tests.helpers import ReboundingDataSource, entry_bars, rebound_bars


def test_cascade_once_refreshes_abt_sell_fill_realized_pnl_from_broker_price() -> None:
    graph = InMemoryGraphStore()
    _position(graph, "held:ABT", "ABT", quantity=98, opened_price_cents=10078)
    ref = open_positions(graph)[0].position_ref
    key = _pending_sell(graph, "ABT", quantity=98, position_ref=ref)
    _empty_pm_run(graph, "refresh-pm")
    broker = _RefreshOnlyBroker(
        (_broker_fill(key, "ABT", quantity=98, price=Decimal("101.35")),)
    )

    cascade_once(graph, provider_agent=_provider(graph), broker=broker)

    fill = graph.get_node("Fill", key)
    assert fill is not None
    assert fill.props["price_cents"] == 1
    assert fill.props["broker_price_cents"] == 10135
    assert fill.props["realized_pnl_cents"] == 5586
    assert graph.list_nodes("Fault") == ()


@dataclass
class _RefreshOnlyBroker:
    broker_fills: tuple[BrokerFill, ...]

    def submit(
        self,
        idempotency_key: str,
        ticker: str,
        side: Literal["buy", "sell"],
        quantity: int,
        limit_price: Money,
    ) -> BrokerFill:
        raise AssertionError("empty PM run must not submit")

    def fills(self) -> tuple[BrokerFill, ...]:
        return self.broker_fills

    def positions(self) -> tuple[BrokerPosition, ...]:
        return ()


def _provider(graph: InMemoryGraphStore) -> ProviderAgent:
    source = ReboundingDataSource(entry=entry_bars(), rebound=rebound_bars())
    return ProviderAgent(
        InProcessBus(),
        graph=graph,
        source=source,
        settings=ProviderSettings(max_staleness_days=7),
    )


def _empty_pm_run(graph: InMemoryGraphStore, run_id: str) -> None:
    order_set = OrderIntentSet(
        run_id=run_id,
        approved=(),
        rejected=(),
        explanation=Explanation(summary="refresh only"),
        provenance=Provenance(
            run_id=run_id,
            source_agent="portfolio_manager",
            graph_node_id=f"PMRun:{run_id}",
        ),
    )
    graph.merge_node(
        "PMRun", run_id, {"order_intent_set": order_set.model_dump(mode="json")}
    )


def _position(
    graph: InMemoryGraphStore,
    key: str,
    ticker: str,
    quantity: int,
    opened_price_cents: int,
) -> None:
    graph.merge_node(
        "Position",
        key,
        {
            "run_id": "seed",
            "ticker": ticker,
            "quantity": quantity,
            "opened_price_cents": opened_price_cents,
            "stop_pct": 0.05,
            "target_pct": 0.10,
            "horizon_days": 10,
            "opened_at": "2026-07-20",
            "status": "open",
        },
    )


def _pending_sell(
    graph: InMemoryGraphStore, ticker: str, *, quantity: int, position_ref: str
) -> str:
    key = f"exit:{position_ref}:{ticker}:sell"
    order = graph.merge_node(
        "OrderIntent",
        f"refresh-pm:{ticker}",
        {
            "ticker": ticker,
            "action": "sell",
            "quantity": quantity,
            "position_ref": position_ref,
        },
    )
    fill = graph.merge_node(
        "Fill",
        key,
        {
            "ticker": ticker,
            "side": "sell",
            "quantity": quantity,
            "price_cents": 1,
            "price_currency": "USD",
            "broker_order_id": f"paper:{key}",
            "status": "pending",
            "reason": None,
        },
    )
    graph.add_edge(fill, order, "EXECUTES")
    return key


def _broker_fill(key: str, ticker: str, *, quantity: int, price: Decimal) -> BrokerFill:
    return BrokerFill(
        idempotency_key=key,
        ticker=ticker,
        side="sell",
        quantity=quantity,
        price=Money(amount=price),
        broker_order_id=f"paper:{key}",
        status="filled",
    )
