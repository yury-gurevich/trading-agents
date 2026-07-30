"""Alpaca paper-trading broker over the execution Broker port.

Agent: execution
Role: submit orders and read fills from Alpaca's paper REST API — the real broker
boundary (ADR-0006), idempotent via client_order_id.
External I/O: HTTPS calls to Alpaca (paper-api.alpaca.markets).
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from decimal import Decimal
from typing import TYPE_CHECKING

from agents.execution import alpaca_orders
from agents.execution.alpaca_positions import positions_from_payload
from agents.execution.broker import BrokerFill, BrokerPosition, BrokerRejectedError
from contracts.common import Money

if TYPE_CHECKING:
    from contracts.common import Ticker

_ORDERS_PATH = "/v2/orders"
_BY_CLIENT_PATH = "/v2/orders:by_client_order_id"
_POSITIONS_PATH = "/v2/positions"

BrokerSide = alpaca_orders.BrokerSide

_order_body = alpaca_orders.order_body
_stop_order_body = alpaca_orders.stop_order_body
_fill_from_order = alpaca_orders.fill_from_order
_price_of = alpaca_orders.price_of


class AlpacaBroker:
    """Alpaca paper-trading broker satisfying the execution Broker port."""

    def __init__(
        self,
        *,
        api_key: str,
        secret_key: str,
        base_url: str,
        timeout: int,
        order_price_tolerance_bps: int = 0,
    ) -> None:
        """Create an Alpaca broker from injected settings."""
        self._api_key = api_key
        self._secret_key = secret_key
        self._base_url = base_url
        self._timeout = timeout
        self._order_price_tolerance_bps = order_price_tolerance_bps

    def submit(
        self,
        idempotency_key: str,
        ticker: Ticker,
        side: BrokerSide,
        quantity: int,
        limit_price: Money,
        tolerance_bps: int | None = None,
    ) -> BrokerFill:
        """Submit one bounded day order under a stable client_order_id; replay dupe."""
        tolerance = (
            self._order_price_tolerance_bps if tolerance_bps is None else tolerance_bps
        )
        order = self._submit_or_get(
            _order_body(
                idempotency_key,
                ticker,
                side,
                quantity,
                limit_price,
                tolerance,
            )
        )
        fill = _fill_from_order(order, idempotency_key, limit_price)
        if fill.status == "rejected":
            raise BrokerRejectedError(fill)
        return fill

    def submit_stop(
        self,
        idempotency_key: str,
        ticker: Ticker,
        side: BrokerSide,
        quantity: int,
        stop_price: Money,
        tif: str = "gtc",
    ) -> BrokerFill:
        """Submit one resting stop order; replay on dupe."""
        order = self._submit_or_get(
            _stop_order_body(idempotency_key, ticker, side, quantity, stop_price, tif)
        )
        fill = _fill_from_order(order, idempotency_key, stop_price)
        if fill.status == "rejected":
            raise BrokerRejectedError(fill)
        return fill

    def fills(self) -> tuple[BrokerFill, ...]:
        """Return broker-known order outcomes for reconciliation."""
        zero = Money(amount=Decimal("0"))
        return tuple(
            _fill_from_order(order, str(order["client_order_id"]), zero)
            for order in self._list_orders()
            if isinstance(order, dict) and order.get("client_order_id")
        )

    def positions(self) -> tuple[BrokerPosition, ...]:
        """Return read-only Alpaca paper holdings for reconciliation."""
        return positions_from_payload(self._request("GET", _POSITIONS_PATH, None))

    def cancel(self, broker_order_id: str) -> None:  # pragma: no cover - real HTTPS
        """Cancel one open order by its broker id (lifecycle/cleanup; ignores body)."""
        request = urllib.request.Request(  # noqa: S310 - hardcoded HTTPS Alpaca endpoint
            f"{self._base_url}{_ORDERS_PATH}/{broker_order_id}",
            headers={
                "APCA-API-KEY-ID": self._api_key,
                "APCA-API-SECRET-KEY": self._secret_key,
            },
            method="DELETE",
        )
        urllib.request.urlopen(  # noqa: S310 - hardcoded HTTPS Alpaca endpoint
            request, timeout=self._timeout
        ).close()

    def _submit_or_get(  # pragma: no cover - real HTTPS
        self, body: dict[str, object]
    ) -> object:
        try:
            return self._request("POST", _ORDERS_PATH, body)
        except urllib.error.HTTPError as exc:
            if exc.code != 422:
                raise RuntimeError(_http_error_message(exc)) from exc
            query = urllib.parse.urlencode(
                {"client_order_id": str(body["client_order_id"])}
            )
            return self._request("GET", f"{_BY_CLIENT_PATH}?{query}", None)

    def _list_orders(self) -> list[object]:  # pragma: no cover - real HTTPS
        query = urllib.parse.urlencode({"status": "all", "limit": 500})
        payload = self._request("GET", f"{_ORDERS_PATH}?{query}", None)
        return payload if isinstance(payload, list) else []

    def _request(  # pragma: no cover - real HTTPS
        self, method: str, path: str, body: dict[str, object] | None
    ) -> object:
        headers = {
            "APCA-API-KEY-ID": self._api_key,
            "APCA-API-SECRET-KEY": self._secret_key,
            "Content-Type": "application/json",
        }
        data = json.dumps(body).encode("utf-8") if body is not None else None
        request = urllib.request.Request(  # noqa: S310 - hardcoded HTTPS Alpaca endpoint
            f"{self._base_url}{path}", data=data, headers=headers, method=method
        )
        with urllib.request.urlopen(  # noqa: S310 - hardcoded HTTPS Alpaca endpoint
            request, timeout=self._timeout
        ) as resp:
            return json.loads(resp.read().decode("utf-8"))


def _http_error_message(exc: urllib.error.HTTPError) -> str:
    body = _http_error_body(exc)
    if body:
        return f"HTTP Error {exc.code}: {exc.reason}: {body}"
    return str(exc)


def _http_error_body(exc: urllib.error.HTTPError) -> str:
    try:
        body = exc.read()
    except OSError:
        return ""
    return body.decode("utf-8", errors="replace").strip()
