"""Alpaca order reads: every page of a listing, and the orders a run start needs.

Agent: execution
Role: list Alpaca orders a page at a time so no listing is cut at the page limit, and
      read a run start's orders: every open order, every order submitted within the
      recent window, and each order the graph still waits on (DL-306).
External I/O: HTTPS to Alpaca through the adapter's injected request callable.
"""

from __future__ import annotations

import urllib.error
import urllib.parse
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING

from agents.execution.alpaca_orders import fill_from_order
from agents.execution.alpaca_replace import http_error_message
from contracts.common import Money

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Mapping

    from agents.execution.broker import BrokerFill
    from agents.execution.run_start_orders import OrderRef

    Request = Callable[[str, str, dict[str, object] | None], object]
    Order = dict[str, object]

# Alpaca's largest page for GET /v2/orders; a full page means there may be more.
PAGE_LIMIT = 500
_ORDERS_PATH = "/v2/orders"
_BY_CLIENT_PATH = "/v2/orders:by_client_order_id"
_NOT_FOUND = 404


def list_orders(
    request: Request, status: str, *, after: str | None = None
) -> list[Order]:
    """Every order one listing names, newest first, read a page at a time.

    Each next page ends before the oldest order of the last (`until`); the read stops
    on a page shorter than the limit or one that adds no order it has not seen.
    """
    orders: dict[str, Order] = {}
    until: str | None = None
    while True:
        page = _page(request, status, after, until)
        fresh = [order for order in page if str(order["id"]) not in orders]
        orders.update((str(order["id"]), order) for order in fresh)
        if len(page) < PAGE_LIMIT or not fresh:
            return list(orders.values())
        until = min(str(order["submitted_at"]) for order in page)


def current_orders(
    request: Request,
    waiting: Iterable[OrderRef],
    *,
    days: int,
    now: datetime | None = None,
) -> list[Order]:
    """Every open order, every order of the last `days`, and each waiting order."""
    since = (now or datetime.now(tz=UTC)) - timedelta(days=days)
    orders = {str(order["id"]): order for order in list_orders(request, "open")}
    for order in list_orders(request, "all", after=since.isoformat()):
        orders.setdefault(str(order["id"]), order)
    keys = {str(order.get("client_order_id", "")) for order in orders.values()}
    for ref in waiting:
        if ref.broker_order_id in orders or ref.idempotency_key in keys:
            continue
        found = order_for(request, ref)
        if found is not None:
            orders[str(found["id"])] = found
            keys.add(str(found.get("client_order_id", "")))
    return sorted(orders.values(), key=_submitted_at, reverse=True)


def order_for(request: Request, ref: OrderRef) -> Order | None:
    """One order by its broker id, else by its client order id; None when unknown.

    The broker's 404 means it holds no such order; any other refusal is raised with
    the broker's own message, so the caller's fault boundary records it.
    """
    if ref.broker_order_id:
        path = f"{_ORDERS_PATH}/{urllib.parse.quote(ref.broker_order_id, safe='')}"
    else:
        query = urllib.parse.urlencode({"client_order_id": ref.idempotency_key})
        path = f"{_BY_CLIENT_PATH}?{query}"
    try:
        order = request("GET", path, None)
    except urllib.error.HTTPError as exc:
        if exc.code == _NOT_FOUND:
            return None
        raise RuntimeError(http_error_message(exc)) from exc
    return order if isinstance(order, dict) and order.get("id") else None


def order_fills(orders: Iterable[object]) -> tuple[BrokerFill, ...]:
    """Map each order that carries a client order id to the broker port's fill."""
    zero = Money(amount=Decimal("0"))
    return tuple(
        fill_from_order(order, str(order["client_order_id"]), zero)
        for order in orders
        if isinstance(order, dict) and order.get("client_order_id")
    )


def _page(
    request: Request, status: str, after: str | None, until: str | None
) -> list[Order]:
    query: dict[str, object] = {
        "status": status,
        "limit": PAGE_LIMIT,
        "direction": "desc",
    }
    if after is not None:
        query["after"] = after
    if until is not None:
        query["until"] = until
    payload = request("GET", f"{_ORDERS_PATH}?{urllib.parse.urlencode(query)}", None)
    if not isinstance(payload, list):
        return []
    return [order for order in payload if isinstance(order, dict) and order.get("id")]


def _submitted_at(order: Mapping[str, object]) -> str:
    return str(order.get("submitted_at", ""))
