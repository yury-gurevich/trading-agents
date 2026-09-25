"""Alpaca in-place stop replacement and HTTP error rendering.

Agent: execution
Role: move a resting stop with Alpaca's atomic PATCH, and render Alpaca errors.
External I/O: HTTPS to Alpaca through the adapter's injected request callable.

Split out of alpaca.py by S230 so the adapter shell stays under the module block.
"""

from __future__ import annotations

import urllib.error
from decimal import Decimal
from typing import TYPE_CHECKING

from agents.execution.alpaca_orders import fill_from_order, replace_body
from agents.execution.broker import BrokerFill, BrokerRejectedError
from contracts.common import Money

if TYPE_CHECKING:
    from collections.abc import Callable

    Request = Callable[[str, str, dict[str, object] | None], object]

_ORDERS_PATH = "/v2/orders"


def replace_stop_order(
    request: Request,
    broker_order_id: str,
    stop_price_cents: int,
    idempotency_key: str,
) -> BrokerFill:
    """PATCH one open stop to a new price; Alpaca answers with the new order.

    Alpaca refuses an `accepted` order with 422 (measured 2026-09-25); that and
    every other HTTP refusal is raised with the broker's own message.
    """
    body = replace_body(stop_price_cents, idempotency_key)
    try:
        order = request("PATCH", f"{_ORDERS_PATH}/{broker_order_id}", body)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(http_error_message(exc)) from exc
    reference = Money(amount=Decimal(str(body["stop_price"])))
    fill = fill_from_order(order, idempotency_key, reference)
    if fill.status == "rejected":
        raise BrokerRejectedError(fill)
    return fill


def http_error_message(exc: urllib.error.HTTPError) -> str:
    """Render an Alpaca HTTP error with its response body when one exists."""
    body = http_error_body(exc)
    if body:
        return f"HTTP Error {exc.code}: {exc.reason}: {body}"
    return str(exc)


def http_error_body(exc: urllib.error.HTTPError) -> str:
    """Return an HTTP error's body, or an empty string when it cannot be read."""
    try:
        body = exc.read()
    except OSError:
        return ""
    return body.decode("utf-8", errors="replace").strip()
