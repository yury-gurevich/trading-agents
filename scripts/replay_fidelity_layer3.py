"""S237 Layer 3: from PM approval to fill, counted from the live record only.

Agent: tooling
Role: count approvals, deliberator overturns, execution outcomes and broker outcomes
      per session; no replay.
External I/O: none.
"""

from __future__ import annotations

from collections import Counter
from typing import TYPE_CHECKING, Any

from contracts.broker_lifecycle import (
    COMPLETED_EXIT_BROKER_STATUSES,
    FILLED_BROKER_STATUSES,
    RESOLVED_UNFILLED_BROKER_STATUSES,
    is_resting_stop_fill,
)
from kernel.graph import Node

if TYPE_CHECKING:
    from collections.abc import Mapping

_OVERTURN = "overturn"  # the only verdict that removes an order (DLIB-OUT-04)


def layer3_row(session: Mapping[str, Any]) -> dict[str, Any]:
    """Return one session's approval-to-fill counts."""
    pm = session.get("pm") or {}
    actions = Counter(str(item.get("action")) for item in pm.get("order_intents") or ())
    verdicts = (session.get("deliberation") or {}).get("verdicts") or {}
    execution = session.get("execution") or {}
    outcomes = Counter(
        _outcome(fill)
        for fill in session.get("fills") or ()
        if not is_resting_stop_fill(Node("Fill", str(fill.get("key", "")), fill))
    )
    return {
        "session": session["session"],
        "approved_buy": actions["buy"],
        "approved_sell": actions["sell"],
        "vetoed": sum(1 for verdict in verdicts.values() if verdict == _OVERTURN),
        "submitted": int(execution.get("submitted", 0)),
        "execution_rejected": int(execution.get("rejected", 0)),
        "execution_skipped": int(execution.get("skipped", 0)),
        "filled": outcomes["filled"],
        "partial": outcomes["partial"],
        "broker_rejected": outcomes["rejected"],
        "dropped": outcomes["dropped"],
        "pending": outcomes["pending"],
    }


def _outcome(fill: Mapping[str, Any]) -> str:
    """The broker's outcome: `broker_status`, since `status` stays `pending`."""
    status = str(fill.get("broker_status") or "").lower()
    if status in FILLED_BROKER_STATUSES:
        return "filled"
    if status in COMPLETED_EXIT_BROKER_STATUSES:
        return "partial"
    if status == "rejected":
        return "rejected"
    if fill.get("drop_reason") or status in RESOLVED_UNFILLED_BROKER_STATUSES:
        return "dropped"  # unfilled in its session (EXEC-OUT-07)
    return "pending"
