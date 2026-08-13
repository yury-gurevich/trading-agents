"""Decide whether a PMRun may be submitted yet, given its deliberation veto.

Agent: execution
Role: hold a BUY-carrying PMRun for a bounded grace period while its DeliberationRun
      may still arrive, and report which of the four outcomes applied.
External I/O: none.

Before this gate, `no DeliberationRun` meant `execute the full set` — so *"the veto
has not run yet"* and *"the veto is not deployed"* were indistinguishable, and the
faster poller won. Measured on 2026-08-08: 18 orders reached the broker at 05:36:22
and the DeliberationRun landed 05:47:32, eleven minutes later, saying *revise*
([DL-98](../../docs/design-log.md)).

**Exits never wait.** The grace applies only when the approved set contains a `buy`.
Blocking an exit on an LLM outage is what S147 refused and what froze the book for
eight days, and ADR-0017 makes the analyst the sole author of exits. A sell-only
PMRun is submitted immediately, exactly as before.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Literal

from contracts.portfolio_manager import OrderIntentSet

if TYPE_CHECKING:
    from agents.execution.settings import ExecutionSettings
    from kernel import GraphStore, Node

DELIBERATED_EDGE = "DELIBERATED_BY"

#: `applied` a real veto was present; `applied_failed_open` a DeliberationRun
#: exists but one or more ticker reviews failed open; `not_required` nothing to
#: veto or sells only; `waiting` a buy is held inside the grace window;
#: `proceeded_unvetoed` the grace expired and the run submitted without a veto.
DeliberationStatus = Literal[
    "applied", "applied_failed_open", "not_required", "waiting", "proceeded_unvetoed"
]


def linked_deliberation(graph: GraphStore, pm_run: Node) -> Node | None:
    """Return the DeliberationRun linked to this PMRun, if the veto has run."""
    return next(
        iter(graph.descendants(pm_run, max_depth=1, edge_types={DELIBERATED_EDGE})),
        None,
    )


def failed_open_tickers(graph: GraphStore, pm_run: Node) -> tuple[str, ...]:
    """Return tickers whose linked deliberation failed open."""
    delib = linked_deliberation(graph, pm_run)
    if delib is None:
        return ()
    return _failed_open_tickers(delib)


def has_buy(order_set: OrderIntentSet) -> bool:
    """Return whether the approved set contains anything that opens exposure."""
    return any(intent.action == "buy" for intent in order_set.approved)


def deliberation_status(
    graph: GraphStore,
    pm_run: Node,
    order_set: OrderIntentSet,
    *,
    now: datetime,
    grace_seconds: int,
) -> DeliberationStatus:
    """Classify this PMRun against its veto, without side effects."""
    delib = linked_deliberation(graph, pm_run)
    if delib is not None:
        if _failed_open_tickers(delib):
            return "applied_failed_open"
        return "applied"
    if not has_buy(order_set):
        return "not_required"
    age = _age_seconds(pm_run, now=now)
    if age is None or age >= grace_seconds:
        return "proceeded_unvetoed"
    return "waiting"


def drop_vetoed(
    graph: GraphStore, pm_run: Node, order_set: OrderIntentSet
) -> OrderIntentSet:
    """Remove deliberation-vetoed tickers from the approved set.

    Execution honours an upstream block; it never decides what to trade
    (EXEC-NEV-01).
    """
    delib = linked_deliberation(graph, pm_run)
    if delib is None:
        return order_set
    vetoed = set(delib.props.get("vetoed_tickers", ()))
    if not vetoed:
        return order_set
    survivors = tuple(i for i in order_set.approved if i.ticker not in vetoed)
    return order_set.model_copy(update={"approved": survivors})


def _failed_open_tickers(delib: Node) -> tuple[str, ...]:
    raw = delib.props.get("failed_open_tickers", ())
    if not isinstance(raw, (list, tuple, set)):
        return ()
    return tuple(item for item in raw if isinstance(item, str))


def _age_seconds(pm_run: Node, *, now: datetime) -> float | None:
    """Seconds since the PMRun was written, or None when it cannot be read.

    An unreadable timestamp must not hold a run forever, so the caller treats None
    as grace-expired and proceeds loudly rather than waiting silently.
    """
    raw = pm_run.props.get("created_at")
    if not isinstance(raw, str):
        return None
    try:
        created = datetime.fromisoformat(raw)
    except ValueError:
        return None
    if created.tzinfo is None:
        return None
    return (now - created).total_seconds()


def is_waiting(
    graph: GraphStore,
    node: Node,
    *,
    now: datetime,
    settings: ExecutionSettings,
) -> bool:
    """Return whether this PMRun is still inside its deliberation grace window."""
    raw = node.props.get("order_intent_set")
    if raw is None:
        return False
    order_set = OrderIntentSet.model_validate(raw)
    status = deliberation_status(
        graph,
        node,
        order_set,
        now=now,
        grace_seconds=settings.deliberation_grace_seconds,
    )
    return status == "waiting"
