"""The brief's orders and fills, read from `Fill` facts as execution wrote them.

Agent: orchestration
Role: select the orders a run placed and the fills that became known in a window.
External I/O: none (reads nodes the caller listed).

A fill's time is `broker_status_refreshed_at`, written when the broker's status
changes. `submitted_at` is not a fill time: it dates a resting stop's placement, and
it is None on stop fills (S234 row 12).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from contracts.broker_lifecycle import FILLED_BROKER_STATUSES, is_resting_stop_fill
from orchestration.daily_brief_text import BriefDataError, FillLine, OrderLine

if TYPE_CHECKING:
    from collections.abc import Iterable

    from kernel import Node

_REJECTED = "rejected"


def run_orders(fills: Iterable[Node], source_run_id: str) -> tuple[OrderLine, ...]:
    """Return the orders whose Fill names this run's PM decision as its source."""
    lines = [
        OrderLine(
            side=_text(fill, "side"),
            quantity=_whole(fill, "quantity"),
            ticker=_text(fill, "ticker"),
            limit_cents=_cents(fill, "order_applied_limit_price_cents"),
            rejected=_status(fill, "broker_status", "status") == _REJECTED,
        )
        for fill in fills
        if fill.props.get("source_run_id") == source_run_id
    ]
    return tuple(sorted(lines, key=lambda line: (line.ticker, line.side)))


def fills_between(
    fills: Iterable[Node], after: datetime | None, until: datetime
) -> tuple[FillLine, ...]:
    """Return fills the broker confirmed after ``after`` and no later than ``until``."""
    found: list[tuple[datetime, FillLine]] = []
    for fill in fills:
        if _status(fill, "broker_status") not in FILLED_BROKER_STATUSES:
            continue
        # A refresh time that cannot be read cannot be placed in any window.
        known = parse_instant(fill.props.get("broker_status_refreshed_at"))
        if known is None or known > until or (after is not None and known <= after):
            continue
        line = FillLine(
            side=_text(fill, "side"),
            quantity=_whole(fill, "quantity"),
            ticker=_text(fill, "ticker"),
            price_cents=_cents(fill, "broker_price_cents"),
            stopped_out=is_resting_stop_fill(fill),
        )
        found.append((known, line))
    return tuple(line for _, line in sorted(found, key=lambda p: (p[0], p[1].ticker)))


def parse_instant(value: object) -> datetime | None:
    """Return an aware instant from an ISO string; a naive one is read as UTC."""
    if not isinstance(value, str):
        return None
    try:
        moment = datetime.fromisoformat(value)
    except ValueError:
        return None
    return moment if moment.tzinfo is not None else moment.replace(tzinfo=UTC)


def _status(fill: Node, *names: str) -> str:
    value = next((fill.props[name] for name in names if fill.props.get(name)), "")
    return str(value).lower()


def _text(fill: Node, name: str) -> str:
    value = fill.props.get(name)
    if not isinstance(value, str) or not value:
        raise BriefDataError(f"Fill.{name}")
    return value


def _whole(fill: Node, name: str) -> int:
    value = fill.props.get(name)
    if not isinstance(value, int) or isinstance(value, bool):
        raise BriefDataError(f"Fill.{name}")
    return value


def _cents(fill: Node, name: str) -> int | None:
    value = fill.props.get(name)
    if value is None:
        return None
    return _whole(fill, name)
