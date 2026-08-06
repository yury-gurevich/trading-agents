"""Graph-derived PortfolioState for PM risk gates.

Agent: portfolio_manager
Role: rebuild held-position awareness from open Position nodes before sizing.
External I/O: none.
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal
from typing import TYPE_CHECKING

from agents.portfolio_manager.portfolio import PortfolioState
from contracts.common import Money
from contracts.positions import active_position_nodes, open_positions

if TYPE_CHECKING:
    from kernel import GraphStore, Node

_SNAPSHOT_LABEL = "BrokerPositionSnapshot"
_CENTS = Decimal("100")
_ZERO = Decimal("0")


def portfolio_from_graph(
    graph: GraphStore, starting_cash: Decimal, *, run_id: str | None = None
) -> PortfolioState:
    """Build PM's starting portfolio from active graph Position nodes."""
    holdings = open_positions(graph)
    positions = {position.ticker: position.quantity for position in holdings}
    position_refs = {position.ticker: position.position_ref for position in holdings}
    snapshot = _latest_snapshot(graph, run_id)
    position_values = _position_values(graph, snapshot)
    if snapshot is None:
        return PortfolioState(
            cash=Money(amount=starting_cash),
            positions=positions,
            position_refs=position_refs,
            position_values=position_values,
        )
    account = _fresh_account(snapshot)
    if account is None:
        return PortfolioState(
            cash=Money(amount=_ZERO),
            positions=positions,
            position_refs=position_refs,
            position_values=position_values,
            account_status="stale",
            account_stale_reason=_account_stale_reason(snapshot),
        )
    return PortfolioState(
        cash=Money(amount=_cents_to_decimal(max(account["equity_cents"], 0))),
        positions=positions,
        position_refs=position_refs,
        position_values=position_values,
        account_cash_cents=account["cash_cents"],
        account_equity_cents=account["equity_cents"],
        account_buying_power_cents=account["buying_power_cents"],
    )


def _latest_snapshot(graph: GraphStore, run_id: str | None) -> Node | None:
    snapshots = [
        node
        for node in graph.list_nodes(_SNAPSHOT_LABEL)
        if run_id is None or node.props.get("run_id") == run_id
    ]
    if not snapshots:
        return None
    return max(snapshots, key=lambda node: str(node.props.get("created_at", "")))


def _fresh_account(snapshot: Node) -> dict[str, int] | None:
    props = snapshot.props
    if props.get("account_status") != "fresh":
        return None
    keys = ("account_cash_cents", "account_equity_cents", "account_buying_power_cents")
    if not all(key in props for key in keys):
        return None
    return {
        "cash_cents": int(props["account_cash_cents"]),
        "equity_cents": int(props["account_equity_cents"]),
        "buying_power_cents": int(props["account_buying_power_cents"]),
    }


def _account_stale_reason(snapshot: Node) -> str:
    props = snapshot.props
    return str(
        props.get("account_stale_reason")
        or props.get("stale_reason")
        or "missing fresh account figures"
    )


def _position_values(graph: GraphStore, snapshot: Node | None) -> dict[str, Money]:
    snapshot_values = _snapshot_values(snapshot)
    values: dict[str, Decimal] = {}
    for position in active_position_nodes(graph):
        cents = _node_market_value_cents(position, snapshot_values)
        if cents > 0:
            ticker = str(position.props["ticker"])
            values[ticker] = values.get(ticker, _ZERO) + _cents_to_decimal(cents)
    return {ticker: Money(amount=amount) for ticker, amount in values.items()}


def _snapshot_values(snapshot: Node | None) -> dict[str, int]:
    if snapshot is None:
        return {}
    values: dict[str, int] = {}
    for item in snapshot.props.get("holdings", ()):
        if not isinstance(item, Mapping):
            continue
        ticker = str(item.get("ticker", ""))
        if ticker:
            values[ticker] = int(item.get("market_value_cents", 0))
    return values


def _node_market_value_cents(position: Node, snapshot_values: dict[str, int]) -> int:
    props = position.props
    if "broker_market_value_cents" in props:
        return int(props["broker_market_value_cents"])
    ticker = str(props["ticker"])
    if ticker in snapshot_values:
        return snapshot_values[ticker]
    return int(props.get("quantity", 0)) * int(props.get("opened_price_cents", 0))


def _cents_to_decimal(cents: int) -> Decimal:
    return Decimal(cents) / _CENTS
