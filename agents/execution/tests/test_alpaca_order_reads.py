"""Alpaca paging, waiting-order reads and configured windows (S283).

Agent: execution
Role: prove complete history reads and bounded run-start reads against a fake account.
External I/O: none.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

import pytest
from pydantic import ValidationError

from agents.execution.alpaca import AlpacaBroker
from agents.execution.alpaca_order_reads import current_orders, list_orders, order_for
from agents.execution.broker_factory import broker_from_settings
from agents.execution.run_start_orders import OrderRef
from agents.execution.settings import ExecutionSettings
from agents.execution.tests.order_read_helpers import NOW, AlpacaAccount, alpaca_order

if TYPE_CHECKING:
    from collections.abc import Callable

_FAKE = "x"


def _aged_account() -> AlpacaAccount:
    stops = [
        alpaca_order(n, days_ago=66, status="new", type="stop", time_in_force="gtc")
        for n in range(1, 35)
    ]
    expired = alpaca_order(
        35, days_ago=98, status="expired", type="stop", time_in_force="gtc"
    )
    return AlpacaAccount(
        stops
        + [expired]
        + [alpaca_order(n, days_ago=(n - 100) / 4) for n in range(100, 1268)]
    )


def _broker(
    monkeypatch: pytest.MonkeyPatch, account: Callable[..., object]
) -> AlpacaBroker:
    broker = AlpacaBroker(
        api_key=_FAKE, secret_key=_FAKE, base_url="https://unused.invalid", timeout=1
    )
    monkeypatch.setattr(broker, "_request", account)
    return broker


def test_a_listing_past_one_page_reads_every_order() -> None:
    """EXEC-OBS-08: A1 - every unique order, descending, in exactly three pages."""
    account = _aged_account()
    expected = sorted(
        account.orders, key=lambda o: str(o["submitted_at"]), reverse=True
    )
    assert list_orders(account, "all") == expected
    assert len(expected) == len({o["id"] for o in expected}) == 1203
    queries = account.listings()
    assert len(queries) == 3
    assert all(q["limit"] == ["500"] and q["direction"] == ["desc"] for q in queries)
    assert "until" not in queries[0]
    assert queries[1]["until"] == [expected[499]["submitted_at"]]


def test_fills_reads_every_order_the_broker_knows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """EXEC-OBS-08: A2 - on-demand fills include the expired, off-page stop."""
    account = _aged_account()
    fills = _broker(monkeypatch, account).fills()
    assert len(fills) == len({f.broker_order_id for f in fills}) == 1203
    assert (
        next(f for f in fills if f.broker_order_id == "order-00035").reason == "expired"
    )


def test_the_run_start_read_holds_open_recent_and_waiting_orders() -> None:
    """EXEC-OBS-08 / EXEC-PERF-03: A3 - the book, recent window and old waiting stop."""
    account = _aged_account()
    orders = current_orders(
        account, (OrderRef("order-00035", "run-00035:T35:buy"),), days=10, now=NOW
    )
    expected_ids = {f"order-{n:05d}" for n in (*range(1, 36), *range(100, 140))}
    assert {o["id"] for o in orders} == expected_ids
    assert len(orders) == 75
    dates = [str(o["submitted_at"]) for o in orders]
    assert dates == sorted(dates, reverse=True)
    assert [q["status"] for q in account.listings()] == [["open"], ["all"]]
    assert account.paths[-1] == "/v2/orders/order-00035"


def test_the_recent_window_starts_the_configured_days_ago() -> None:
    """EXEC-PERF-03: A4 - the window uses the requested number of days."""
    account = _aged_account()
    current_orders(account, (), days=12, now=NOW)
    assert account.listings()[1]["after"] == [(NOW - timedelta(days=12)).isoformat()]


def test_an_order_already_listed_is_read_once() -> None:
    """EXEC-PERF-03: A5 - overlapping listings and refs add no duplicate read."""
    order = alpaca_order(1, days_ago=1, status="new")
    account = AlpacaAccount([order])
    refs = (
        OrderRef("order-00001", "run-00001:T1:buy"),
        OrderRef("", "run-00001:T1:buy"),
    )
    assert current_orders(account, refs, days=10, now=NOW) == [order]
    assert len(account.paths) == len(account.listings()) == 2


def test_a_waiting_order_with_no_broker_id_is_read_by_its_client_order_id() -> None:
    """EXEC-OBS-08: A6 - an old cancelled order is resolved by its encoded key."""
    order = alpaca_order(7, days_ago=200, status="canceled")
    account = AlpacaAccount([order])
    ref = OrderRef("", "run-00007:T7:buy")
    assert current_orders(account, (ref, ref), days=10, now=NOW) == [order]
    assert (
        account.paths[-1]
        == "/v2/orders:by_client_order_id?client_order_id=run-00007%3AT7%3Abuy"
    )
    assert len(account.paths) == 3


def test_a_waiting_order_the_broker_does_not_know_is_left_out() -> None:
    """EXEC-OBS-08: A7 - unknown ids and keys are harmless 404s; malformed is absent."""
    account = AlpacaAccount([])
    refs = (OrderRef("unknown", "key"), OrderRef("", "unknown:key"))
    assert current_orders(account, refs, days=10, now=NOW) == []
    assert len(account.paths) == 4
    for answer in (None, {"no": "id"}):
        assert order_for(lambda *_, answer=answer: answer, refs[0]) is None


def test_any_other_refusal_of_an_order_read_is_raised() -> None:
    """EXEC-OBS-02: A8 - a 500 keeps its status, reason and broker response body."""
    message = 'HTTP Error 500: refused: {"message":"internal"}'
    with pytest.raises(RuntimeError, match=re.escape(message)):
        current_orders(
            AlpacaAccount([], fail=500), (OrderRef("missing", "key"),), days=10, now=NOW
        )


def test_the_window_is_a_bounded_setting_the_factory_hands_on(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """EXEC-PERF-03: A9 - default, both bounds, factory and adapter forwarding."""
    assert ExecutionSettings().broker_recent_order_days == 10
    for days in (3, 61):
        with pytest.raises(ValidationError, match="broker_recent_order_days"):
            ExecutionSettings(broker_recent_order_days=days)
    settings = ExecutionSettings(
        alpaca_api_key=_FAKE, alpaca_secret_key=_FAKE, broker_recent_order_days=7
    )
    broker = broker_from_settings(settings)
    assert isinstance(broker, AlpacaBroker)
    account = AlpacaAccount([])
    monkeypatch.setattr(broker, "_request", account)
    expected = datetime.now(tz=UTC) - timedelta(days=7)
    assert broker.current_orders() == ()
    after = datetime.fromisoformat(account.listings()[1]["after"][0])
    assert abs((after - expected).total_seconds()) < 5
