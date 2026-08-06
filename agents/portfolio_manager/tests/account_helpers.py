"""Portfolio Manager account-sizing test helpers.

Agent: portfolio_manager
Role: build account snapshots, positions, market data, and regime fixtures.
External I/O: none.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from agents.portfolio_manager.tests.helpers import bar
from contracts.common import Provenance
from contracts.provider import DataQualityTrace, MarketData, RegimeContext

if TYPE_CHECKING:
    from kernel import InMemoryGraphStore


def snapshot(
    graph: InMemoryGraphStore,
    run_id: str,
    *,
    equity_cents: int = 10000000,
    cash_cents: int | None = None,
    buying_power_cents: int | None = None,
    status: str = "fresh",
    account_status: str = "fresh",
    include_account: bool = True,
) -> None:
    props: dict[str, object] = {
        "run_id": run_id,
        "status": status,
        "account_status": account_status,
        "created_at": datetime.now(tz=UTC).isoformat(),
        "holding_count": 0,
        "holdings": [],
    }
    if status == "stale":
        props["stale_reason"] = "broker account read failed: RuntimeError"
        props["account_stale_reason"] = "broker account read failed: RuntimeError"
    if not include_account:
        graph.merge_node("BrokerPositionSnapshot", f"snapshot:{run_id}", props)
        return
    if account_status == "fresh" and cash_cents is not None:
        props["account_cash_cents"] = cash_cents
        props["account_equity_cents"] = equity_cents
        props["account_buying_power_cents"] = buying_power_cents or equity_cents
    elif account_status == "fresh" and status == "fresh":
        props["account_cash_cents"] = equity_cents
        props["account_equity_cents"] = equity_cents
        props["account_buying_power_cents"] = buying_power_cents or equity_cents
    graph.merge_node("BrokerPositionSnapshot", f"snapshot:{run_id}", props)


def position(
    graph: InMemoryGraphStore,
    key: str,
    ticker: str,
    quantity: int,
    *,
    market_value_cents: int,
) -> None:
    graph.merge_node(
        "Position",
        key,
        {
            "ticker": ticker,
            "quantity": quantity,
            "opened_price_cents": round(market_value_cents / quantity),
            "broker_market_value_cents": market_value_cents,
            "status": "open",
        },
    )


def market(ticker: str) -> MarketData:
    return MarketData(
        bars=(bar(ticker, 0, 100.0),),
        quality=DataQualityTrace(requested=1, returned=1),
        provenance=Provenance(run_id="provider", source_agent="provider"),
    )


def regime() -> RegimeContext:
    return RegimeContext(
        label="neutral",
        as_of=datetime.now(tz=UTC),
        base_min_confidence=0.55,
        base_stop_loss_pct=0.05,
        base_take_profit_pct=0.10,
        base_max_holding_days=10,
        provenance=Provenance(run_id="provider", source_agent="provider"),
    )
