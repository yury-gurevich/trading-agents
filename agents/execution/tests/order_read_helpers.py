"""Deterministic account and ageing-stop doubles for Sprint 283.

Agent: execution
Role: model exclusive Alpaca pages and old stops hidden by a one-page read.
External I/O: none.
"""

from __future__ import annotations

import urllib.error
import urllib.parse
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from email.message import Message
from io import BytesIO
from typing import TYPE_CHECKING, Literal

from agents.execution.broker import BrokerFill
from agents.execution.tests.broker_stop_helpers import TrackingBroker

if TYPE_CHECKING:
    from collections.abc import Sequence

    from agents.execution.run_start_orders import OrderRef
    from contracts.common import Money

NOW = datetime(2026, 12, 7, 22, 30, tzinfo=UTC)
_OPEN = frozenset({"new", "accepted", "pending_new", "partially_filled", "held"})


def alpaca_order(
    n: int, *, days_ago: float, status: str = "filled", **changes: object
) -> dict[str, object]:
    """Return one raw order with a unique submission timestamp."""
    return {
        "id": f"order-{n:05d}",
        "client_order_id": f"run-{n:05d}:T{n}:buy",
        "symbol": f"T{n}",
        "side": "buy",
        "qty": "1",
        "filled_qty": "1" if status == "filled" else "0",
        "filled_avg_price": "100.00" if status == "filled" else None,
        "type": "limit",
        "time_in_force": "day",
        "status": status,
        "submitted_at": (NOW - timedelta(days=days_ago, seconds=n)).isoformat(),
        **changes,
    }


class AlpacaAccount:
    """Serve listings and individual orders without a live broker."""

    def __init__(self, orders: list[dict[str, object]], *, fail: int = 0) -> None:
        self.orders = orders
        self.fail = fail
        self.paths: list[str] = []

    def __call__(
        self, method: str, path: str, body: dict[str, object] | None
    ) -> object:
        assert method == "GET"
        assert body is None
        self.paths.append(path)
        url = urllib.parse.urlsplit(path)
        query = urllib.parse.parse_qs(url.query)
        if url.path == "/v2/orders":
            return self._listing(query)
        if not self.fail:
            for order in self.orders:
                if url.path == "/v2/orders:by_client_order_id":
                    matches = order["client_order_id"] == query["client_order_id"][0]
                else:
                    matches = order["id"] == urllib.parse.unquote(
                        url.path.rsplit("/", 1)[1]
                    )
                if matches:
                    return order
        raise urllib.error.HTTPError(
            path,
            self.fail or 404,
            "refused",
            Message(),
            BytesIO(b'{"message":"internal"}'),
        )

    def _listing(self, query: dict[str, list[str]]) -> list[dict[str, object]]:
        status = query.get("status", ["open"])[0]
        orders = [
            order
            for order in self.orders
            if status == "all" or (order["status"] in _OPEN) == (status == "open")
        ]
        if "after" in query:
            after = datetime.fromisoformat(query["after"][0])
            orders = [
                o
                for o in orders
                if datetime.fromisoformat(str(o["submitted_at"])) > after
            ]
        if "until" in query:
            until = datetime.fromisoformat(query["until"][0])
            orders = [
                o
                for o in orders
                if datetime.fromisoformat(str(o["submitted_at"])) < until
            ]
        orders.sort(
            key=lambda o: str(o["submitted_at"]),
            reverse=query.get("direction", ["desc"])[0] == "desc",
        )
        return orders[: int(query.get("limit", ["50"])[0])]

    def listings(self) -> list[dict[str, list[str]]]:
        """Return each listing's decoded query, preserving request order."""
        return [
            urllib.parse.parse_qs(urllib.parse.urlsplit(path).query)
            for path in self.paths
            if urllib.parse.urlsplit(path).path == "/v2/orders"
        ]


class AgedAccountBroker(TrackingBroker):
    """Keep old terminal stops by id while hiding them from the newest page."""

    def __init__(self) -> None:
        super().__init__()
        self.hidden: set[str] = set()
        self.waited_on: list[tuple[tuple[str, str], ...]] = []

    def submit_stop(
        self,
        idempotency_key: str,
        ticker: str,
        side: Literal["buy", "sell"],
        quantity: int,
        stop_price: Money,
        tif: str = "gtc",
    ) -> BrokerFill:
        fill = BrokerFill(
            idempotency_key=idempotency_key,
            ticker=ticker,
            side=side,
            quantity=quantity,
            price=stop_price,
            broker_order_id=f"broker:{idempotency_key}",
            status="pending",
            submitted_at=NOW.isoformat(),
            order_type="stop",
            time_in_force=tif,
            order_status="new",
        )
        self.broker_fills += (fill,)
        return fill

    def expire(self, broker_order_id: str, *, beyond_page: bool) -> None:
        """Expire a stop, optionally moving its terminal outcome off the page."""
        self.broker_fills = tuple(
            replace(fill, status="rejected", order_status="expired", reason="expired")
            if fill.broker_order_id == broker_order_id
            else fill
            for fill in self.broker_fills
        )
        if beyond_page:
            self.hidden.add(broker_order_id)

    def fills(self) -> tuple[BrokerFill, ...]:
        return tuple(
            f for f in self.broker_fills if f.broker_order_id not in self.hidden
        )

    def current_orders(
        self, waiting: Sequence[OrderRef] = ()
    ) -> tuple[BrokerFill, ...]:
        self.waited_on.append(
            tuple((r.broker_order_id, r.idempotency_key) for r in waiting)
        )
        ids = {r.broker_order_id for r in waiting if r.broker_order_id}
        keys = {r.idempotency_key for r in waiting}
        return tuple(
            f
            for f in self.broker_fills
            if f.status == "pending"
            or f.broker_order_id in ids
            or f.idempotency_key in keys
        )

    def live_stops(self) -> tuple[BrokerFill, ...]:
        return tuple(
            f
            for f in self.broker_fills
            if f.status == "pending" and f.order_type == "stop"
        )
