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
    from collections.abc import Collection

    from kernel import GraphStore, Node


@dataclass(frozen=True)
class Readiness:
    """The current dispatcher-safe interpretation of a fleet preflight."""

    state: Literal["ready", "degraded", "failing", "unknown"]
    preflight_key: str
    checked_at: str
    failures: tuple[str, ...]


def fleet_readiness(
    graph: GraphStore,
    *,
    now: datetime,
    max_age_minutes: int,
    degradable_agents: Collection[str] = (),
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
    if node.props.get("passed") is True:
        state: Literal["ready", "degraded", "failing"] = "ready"
    elif _all_failures_degradable(failures, degradable_agents):
        state = "degraded"
    else:
        state = "failing"
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


def _all_failures_degradable(
    failures: tuple[str, ...], degradable_agents: Collection[str]
) -> bool:
    """Return whether every failure belongs to a declared degradable agent."""
    if not failures or not degradable_agents:
        return False
    return all(_is_degradable_failure(item, degradable_agents) for item in failures)


def _is_degradable_failure(failure: str, agents: Collection[str]) -> bool:
    parts = failure.split(":", 3)
    if len(parts) != 4:
        return False
    kind, agent_type, check, reason = parts
    return (
        kind in {"unrecoverable", "unexpected", "transient"}
        and agent_type in agents
        and bool(check)
        and bool(reason)
    )
