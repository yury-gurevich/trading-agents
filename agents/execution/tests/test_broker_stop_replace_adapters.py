"""The Broker port's in-place stop replace, per adapter (S230).

Agent: execution
Role: pin Alpaca's PATCH shape against a recorded response, the paper model of
      Alpaca's 422, and the replace path's unreadable/unknown-order edges.
External I/O: none - the worktree has no network; the live replace is the
      planner's pre-merge check.
"""

from __future__ import annotations

import urllib.error
from decimal import Decimal
from email.message import Message
from io import BytesIO
from types import MethodType
from typing import TYPE_CHECKING

import pytest

from agents.execution.alpaca import AlpacaBroker
from agents.execution.broker import BrokerFill, BrokerRejectedError
from agents.execution.paper_broker import PaperBroker
from agents.execution.tests.stop_realign_helpers import (
    RecordingPaperBroker,
    run_placement,
    seed_usb,
    seed_usb_stop,
)
from contracts.broker_stops import active_broker_stop_orders
from contracts.common import Money
from kernel import InMemoryGraphStore

if TYPE_CHECKING:
    from collections.abc import Callable

_NEW_KEY = "stop:ref:USB#1"
_FIXTURE_CREDENTIAL = "not-a-credential"
# Alpaca's documented replace answer: a new order that `replaces` the old id.
_RECORDED_REPLACE = {
    "id": "b7f1-new",
    "client_order_id": _NEW_KEY,
    "symbol": "USB",
    "side": "sell",
    "qty": "16",
    "type": "stop",
    "time_in_force": "gtc",
    "stop_price": "58.06",
    "status": "new",
    "replaces": "a3c9-old",
    "filled_avg_price": None,
}


def test_alpaca_replace_patches_the_stop_price_under_the_new_key() -> None:
    """EXEC-OBS-06 / EXEC-DEP-04: one PATCH; the answer is the new order."""
    broker, seen = _alpaca(lambda: _RECORDED_REPLACE)

    fill = broker.replace_stop("a3c9-old", 5806, idempotency_key=_NEW_KEY)

    assert seen == [
        (
            "PATCH",
            "/v2/orders/a3c9-old",
            {"stop_price": "58.06", "client_order_id": _NEW_KEY},
        )
    ]
    assert (fill.idempotency_key, fill.broker_order_id) == (_NEW_KEY, "b7f1-new")
    assert (fill.status, fill.order_status, fill.order_type) == (
        "pending",
        "new",
        "stop",
    )
    assert fill.price == Money(amount=Decimal("58.06"))


def test_alpaca_refusal_carries_the_broker_message() -> None:
    """EXEC-OBS-06: Alpaca's 422 for an accepted order surfaces verbatim."""
    body = b'{"code":42210000,"message":"cannot replace order in accepted status"}'

    def refuse() -> object:
        raise urllib.error.HTTPError(
            "https://paper", 422, "Unprocessable Entity", Message(), BytesIO(body)
        )

    broker, _seen = _alpaca(refuse)

    with pytest.raises(RuntimeError, match="cannot replace order in accepted status"):
        broker.replace_stop("a3c9-old", 5806, idempotency_key=_NEW_KEY)


def test_alpaca_rejected_replacement_raises() -> None:
    """EXEC-OBS-06: a rejected replacement is never recorded as a live stop."""
    broker, _seen = _alpaca(lambda: {**_RECORDED_REPLACE, "status": "rejected"})

    with pytest.raises(BrokerRejectedError):
        broker.replace_stop("a3c9-old", 5806, idempotency_key=_NEW_KEY)


def test_paper_broker_models_alpacas_refusal_of_an_accepted_stop() -> None:
    """EXEC-OBS-06: the paper broker refuses what Alpaca refuses (422)."""
    broker = PaperBroker(stop_order_status="accepted")
    stop = broker.submit_stop("stop:ref:USB", "USB", "sell", 16, _money("57.47"))

    with pytest.raises(RuntimeError, match="422 cannot replace order in accepted"):
        broker.replace_stop(stop.broker_order_id, 5806, idempotency_key=_NEW_KEY)
    with pytest.raises(LookupError):
        broker.replace_stop("paper:missing", 5806, idempotency_key=_NEW_KEY)


def test_unreadable_broker_orders_leave_every_stop_and_fault() -> None:
    """EXEC-OBS-06 / EXEC-OBS-03: no status, no replace; the old stop stays."""
    graph = InMemoryGraphStore()
    broker = _UnreadableBroker()
    seed_usb(graph)
    old_key = seed_usb_stop(graph, broker)

    sink = run_placement(graph, broker)

    assert broker.replace_calls == []
    assert [stop.key for stop in active_broker_stop_orders(graph)] == [old_key]
    assert [fault.error_type for fault in sink.faults] == ["StopReplaceFailed"]
    assert "orders endpoint down" in sink.faults[0].message


def test_a_stop_the_broker_does_not_list_is_skipped_as_unknown() -> None:
    """EXEC-OBS-06: an order whose status cannot be read is not replaced."""
    graph = InMemoryGraphStore()
    broker = _UnlistedBroker()
    seed_usb(graph)
    seed_usb_stop(graph, broker)

    sink = run_placement(graph, broker)

    assert broker.replace_calls == []
    assert [fault.error_type for fault in sink.faults] == ["StopReplaceSkipped"]
    assert sink.faults[0].context["order_status"] == "unknown"


class _UnreadableBroker(RecordingPaperBroker):
    def fills(self) -> tuple[BrokerFill, ...]:
        raise RuntimeError("orders endpoint down")


class _UnlistedBroker(RecordingPaperBroker):
    def fills(self) -> tuple[BrokerFill, ...]:
        return ()


def _alpaca(
    answer: Callable[[], object],
) -> tuple[AlpacaBroker, list[tuple[object, ...]]]:
    broker = AlpacaBroker(
        api_key="k",
        secret_key=_FIXTURE_CREDENTIAL,
        base_url="https://paper",
        timeout=1,
    )
    seen: list[tuple[object, ...]] = []

    def fake_request(
        _self: AlpacaBroker, method: str, path: str, body: dict[str, object] | None
    ) -> object:
        seen.append((method, path, body))
        return answer()

    broker._request = MethodType(fake_request, broker)  # type: ignore[method-assign]
    return broker, seen


def _money(amount: str) -> Money:
    return Money(amount=Decimal(amount))
