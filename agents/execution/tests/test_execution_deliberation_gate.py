"""The veto gates buys, never exits (DL-98).

Agent: execution
Role: pin the bounded hold for a buy-carrying PMRun, the immediate pass for a
      sell-only one, and the loud record when the grace expires unvetoed.
External I/O: none.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Literal

from agents.execution.deliberation_gate import deliberation_status, drop_vetoed
from agents.execution.poll import find_pending
from agents.execution.settings import ExecutionSettings
from contracts.common import Explanation, Money, Provenance
from contracts.portfolio_manager import OrderIntent, OrderIntentSet
from kernel import InMemoryGraphStore, Node

NOW = datetime(2026, 8, 10, 22, 40, tzinfo=UTC)
GRACE = 900


def _intent(ticker: str, action: Literal["buy", "sell"]) -> OrderIntent:
    return OrderIntent(
        ticker=ticker,
        action=action,
        quantity=5,
        est_price=Money(amount=Decimal("100.00")),
        stop_pct=0.05,
        target_pct=0.10,
        rationale=Explanation(summary="fixture"),
    )


def _order_set(*intents: OrderIntent) -> OrderIntentSet:
    return OrderIntentSet(
        run_id="pm-run-fixture",
        approved=intents,
        rejected=(),
        explanation=Explanation(summary="fixture"),
        provenance=Provenance(
            run_id="pm-run-fixture",
            source_agent="portfolio_manager",
            graph_node_id="PMRun:pm-run-fixture",
        ),
    )


def _pm_run(graph: InMemoryGraphStore, *, age_seconds: int) -> Node:
    created = (NOW - timedelta(seconds=age_seconds)).isoformat()
    return graph.merge_node("PMRun", "pm-run-fixture", {"created_at": created})


def _status(
    graph: InMemoryGraphStore,
    node: Node,
    order_set: OrderIntentSet,
    grace: int = GRACE,
) -> str:
    return deliberation_status(graph, node, order_set, now=NOW, grace_seconds=grace)


def test_a_buy_waits_while_its_veto_may_still_arrive() -> None:
    """EXEC-NEV-01 / DL-98: inside the grace window a buy is held, not submitted.

    Measured 2026-08-08: 18 orders reached the broker 11 minutes before the
    DeliberationRun that said `revise` was written.
    """
    graph = InMemoryGraphStore()
    node = _pm_run(graph, age_seconds=60)

    assert _status(graph, node, _order_set(_intent("AAPL", "buy"))) == "waiting"


def test_an_exit_never_waits_for_the_veto() -> None:
    """S147 / ADR-0017: blocking an exit on an LLM outage is what froze the book.

    A sell-only PMRun is submitted immediately however young it is.
    """
    graph = InMemoryGraphStore()
    node = _pm_run(graph, age_seconds=0)

    assert _status(graph, node, _order_set(_intent("AAPL", "sell"))) == "not_required"


def test_a_mixed_run_waits_because_it_carries_a_buy() -> None:
    graph = InMemoryGraphStore()
    node = _pm_run(graph, age_seconds=60)
    order_set = _order_set(_intent("AAPL", "buy"), _intent("MSFT", "sell"))

    assert _status(graph, node, order_set) == "waiting"


def test_the_wait_is_bounded_and_then_proceeds() -> None:
    """Fail-open is still the policy: the grace expires, it never blocks forever."""
    graph = InMemoryGraphStore()
    node = _pm_run(graph, age_seconds=GRACE + 1)

    status = _status(graph, node, _order_set(_intent("AAPL", "buy")))
    assert status == "proceeded_unvetoed"


def test_a_linked_veto_ends_the_wait_immediately() -> None:
    graph = InMemoryGraphStore()
    node = _pm_run(graph, age_seconds=1)
    delib = graph.merge_node("DeliberationRun", "pm-run-fixture", {})
    graph.add_edge(node, delib, "DELIBERATED_BY")

    assert _status(graph, node, _order_set(_intent("AAPL", "buy"))) == "applied"


def test_an_unreadable_timestamp_proceeds_rather_than_waiting_forever() -> None:
    """A PMRun with no usable `created_at` must not be held indefinitely."""
    graph = InMemoryGraphStore()
    node = graph.merge_node("PMRun", "pm-run-fixture", {})

    status = _status(graph, node, _order_set(_intent("AAPL", "buy")))
    assert status == "proceeded_unvetoed"


def test_zero_grace_restores_the_previous_race_deliberately() -> None:
    """`deliberation_grace_seconds=0` is the documented escape hatch."""
    graph = InMemoryGraphStore()
    node = _pm_run(graph, age_seconds=0)

    status = _status(graph, node, _order_set(_intent("AAPL", "buy")), grace=0)
    assert status == "proceeded_unvetoed"


def test_drop_vetoed_removes_only_the_vetoed_tickers() -> None:
    graph = InMemoryGraphStore()
    node = _pm_run(graph, age_seconds=1)
    delib = graph.merge_node(
        "DeliberationRun", "pm-run-fixture", {"vetoed_tickers": ["MSFT"]}
    )
    graph.add_edge(node, delib, "DELIBERATED_BY")
    order_set = _order_set(_intent("AAPL", "buy"), _intent("MSFT", "buy"))

    survivors = drop_vetoed(graph, node, order_set)

    assert [i.ticker for i in survivors.approved] == ["AAPL"]


def test_the_default_grace_is_bounded_and_settable() -> None:
    """The tunable exists with a real bound, so it cannot be set to forever."""
    settings = ExecutionSettings()
    assert settings.deliberation_grace_seconds == 900
    field = type(settings).model_fields["deliberation_grace_seconds"]
    assert any(getattr(m, "le", None) == 3600 for m in field.metadata)


def test_a_malformed_timestamp_proceeds_rather_than_waiting() -> None:
    """An unparseable `created_at` must not be able to stall trading."""
    graph = InMemoryGraphStore()
    node = graph.merge_node("PMRun", "pm-run-fixture", {"created_at": "not-a-date"})

    status = _status(graph, node, _order_set(_intent("AAPL", "buy")))
    assert status == "proceeded_unvetoed"


def test_a_naive_timestamp_proceeds_rather_than_waiting() -> None:
    """A tz-naive `created_at` cannot be compared to an aware now, so do not wait."""
    graph = InMemoryGraphStore()
    node = graph.merge_node(
        "PMRun", "pm-run-fixture", {"created_at": "2026-08-10T22:39:00"}
    )

    status = _status(graph, node, _order_set(_intent("AAPL", "buy")))
    assert status == "proceeded_unvetoed"


def test_find_pending_holds_back_a_waiting_pm_run() -> None:
    """DL-98: the wait is expressed by leaving the PMRun unconsumed, so a later
    poll retries it once the veto lands."""
    graph = InMemoryGraphStore()
    order_set = _order_set(_intent("AAPL", "buy"))
    node = graph.merge_node(
        "PMRun",
        "pm-run-fixture",
        {
            "created_at": datetime.now(tz=UTC).isoformat(),
            "order_intent_set": order_set.model_dump(mode="json"),
        },
    )

    assert find_pending(graph) == []

    delib = graph.merge_node("DeliberationRun", "pm-run-fixture", {})
    graph.add_edge(node, delib, "DELIBERATED_BY")
    assert [n.key for n in find_pending(graph)] == ["pm-run-fixture"]
