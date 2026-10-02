"""A run's book window over the broker's fills.

Agent: reporter
Role: place filled Fills in a PM run's window and count what the broker did.
External I/O: none.

A fill's time is `broker_status_refreshed_at`, written when the broker's status
changes; `submitted_at` dates an order's placement and is not a fill time, and
`status` stays `pending` after a fill, so only `broker_status` is read (S234).
A run's window runs after the previous PMRun's `created_at`, up to and including
its own, so each filled fill belongs to exactly one run (DL-262, RPT-IDM-04).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from contracts.broker_lifecycle import FILLED_BROKER_STATUSES, is_resting_stop_fill

if TYPE_CHECKING:
    from collections.abc import Iterable

    from kernel import Node

type TimedFill = tuple[datetime, Node]


def utc_instant(value: object) -> datetime | None:
    """Return an aware UTC instant from an ISO string; a naive one is read as UTC."""
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return (
        parsed.replace(tzinfo=UTC) if parsed.tzinfo is None else parsed.astimezone(UTC)
    )


def window_start(pm_runs: Iterable[Node], reported_at: datetime) -> datetime | None:
    """Return the latest PMRun `created_at` strictly before ``reported_at``."""
    earlier = (
        moment
        for run in pm_runs
        if (moment := utc_instant(run.props.get("created_at"))) is not None
        and moment < reported_at
    )
    return max(earlier, default=None)


def filled_fills(fills: Iterable[Node]) -> tuple[TimedFill, ...]:
    """Return the fills the broker filled, each with the time it became known."""
    # A refresh time that cannot be read cannot be placed in any window.
    return tuple(
        (moment, fill)
        for fill in fills
        if str(fill.props.get("broker_status") or "").lower() in FILLED_BROKER_STATUSES
        and (moment := utc_instant(fill.props.get("broker_status_refreshed_at")))
        is not None
    )


def fills_between(
    timed: Iterable[TimedFill], after: datetime | None, until: datetime
) -> tuple[Node, ...]:
    """Return the fills known after ``after`` (exclusive) and by ``until``."""
    return tuple(
        fill
        for moment, fill in timed
        if moment <= until and (after is None or moment > after)
    )


def exits_since(
    timed: Iterable[TimedFill], since: datetime, until: datetime
) -> tuple[Node, ...]:
    """Return the sell fills known from ``since`` (inclusive) to ``until``."""
    return tuple(
        fill
        for moment, fill in timed
        if since <= moment <= until and fill.props.get("side") == "sell"
    )


def book_counts(window: tuple[Node, ...]) -> dict[str, float]:
    """Count the positions opened and closed in a window, and the stops among them."""
    sells = tuple(fill for fill in window if fill.props.get("side") == "sell")
    return {
        "positions_opened": float(
            sum(fill.props.get("side") == "buy" for fill in window)
        ),
        "positions_closed": float(len(sells)),
        "close_trigger_stop": float(sum(is_resting_stop_fill(fill) for fill in sells)),
    }
