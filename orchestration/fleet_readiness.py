"""Read master-owned fleet readiness facts for dispatcher and dashboard decisions.

Agent: orchestration
Role: derive current fleet readiness from immutable master preflight evidence.
External I/O: reads the injected GraphStore only.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from kernel import GraphStore, Node


@dataclass(frozen=True)
class Readiness:
    """The current dispatcher-safe interpretation of a fleet preflight."""

    state: Literal["ready", "failing", "unknown"]
    preflight_key: str
    checked_at: str
    failures: tuple[str, ...]


def fleet_readiness(
    graph: GraphStore, *, now: datetime, max_age_minutes: int
) -> Readiness:
    """Return readiness from the newest parseable master FleetPreflight fact."""
    latest: tuple[datetime, Node] | None = None
    for node in graph.list_nodes("FleetPreflight"):
        checked_at = _checked_at(node)
        if checked_at is not None and (latest is None or checked_at > latest[0]):
            latest = (checked_at, node)
    if latest is None:
        return Readiness("unknown", "", "", ())

    checked_at, node = latest
    checked_value = str(node.props.get("checked_at", ""))
    if now - checked_at > timedelta(minutes=max_age_minutes):
        return Readiness("unknown", node.key, checked_value, ())
    failures = tuple(str(value) for value in node.props.get("failures", ()))
    state: Literal["ready", "failing"] = (
        "ready" if node.props.get("passed") is True else "failing"
    )
    return Readiness(state, node.key, checked_value, failures)


def is_active_run_hold(node: Node) -> bool:
    """Return whether immutable hold evidence has not yet been released."""
    return node.props.get("state") == "held" and "released_at" not in node.props


def _checked_at(node: Node) -> datetime | None:
    raw = node.props.get("checked_at")
    if not isinstance(raw, str):
        return None
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None
