"""The records human actions leave in the graph, each with its kind and instant.

Agent: surfaces
Role: list every recorded human action, and read every stored time one way.
External I/O: injected GraphStore reads only.

Kinds (S236 Scope 4; DL-235 decisions 6 and 7): `command` (a CommandAudit whose
Intent acts, or an interpret call that produced none), `run` (a RunRequest outside the
schedule), `resume`, `hold_answer`, `escalation`, and `deploy` (a change, reported
beside the rest).
Reading is never an action: a `status` or `explain` intent, or an explain call, which
the operator audits with no Intent (OPR-OUT-06).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, date, datetime, time
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from kernel import GraphStore, Node

ActionKind = Literal["command", "run", "resume", "hold_answer", "escalation", "deploy"]
DEPLOY: ActionKind = "deploy"
# The reading families of contracts/operator.py's IntentFamily; every other one acts.
READING_FAMILIES = frozenset({"status", "explain"})
_EXPLAIN_CALL = "explain"  # the outcome the operator audits an explain call with
_SCHEDULED = "sched-"
_BARE_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
# Labels whose every node is one human action, and the property that times it.
_STAMPED: tuple[tuple[str, ActionKind, str], ...] = (
    ("Escalation", "escalation", "created_at"),
    ("DeployRecord", "deploy", "deployed_at"),
)


class ScorecardDataError(ValueError):
    """A record the scorecard must place in time carries no readable time."""


@dataclass(frozen=True)
class HumanAction:
    """One record a human action left: its kind, when, and the run it names if any.

    Only a hold answer names its run: the run it releases is placed after the answer,
    so the answer belongs to that run's session, not the next one (DL-235).
    """

    kind: ActionKind
    at: datetime
    run_id: str = ""


def instant(value: object, tick: time, *, label: str) -> datetime:
    """Read a stored time as an aware UTC instant, the one way every time is read.

    A naive time is UTC (`RunRequest.requested_at` is written without an offset). A
    bare date carries no time at all, so it reads as the dispatcher's placing tick on
    that date (the operator's decision, DL-235 decision 5).
    """
    text = value if isinstance(value, str) else ""
    try:
        if _BARE_DATE.fullmatch(text):
            return datetime.combine(date.fromisoformat(text), tick, UTC)
        parsed = datetime.fromisoformat(text)
    except ValueError:
        raise ScorecardDataError(f"one {label} carries no readable time") from None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def human_actions(graph: GraphStore, tick: time) -> tuple[HumanAction, ...]:
    """Return every recorded human action, whenever it happened; reading excluded."""
    actions = [
        HumanAction("command", _at(node, "created_at", tick))
        for node in graph.list_nodes("CommandAudit")
        if _acts(graph, node)
    ]
    actions.extend(_requested(node, tick) for node in _off_schedule(graph))
    actions.extend(
        HumanAction(
            "hold_answer",
            _at(node, "answered_at", tick),
            str(node.props.get("run_id", "")),
        )
        for node in graph.list_nodes("RunHoldAnswer")
    )
    actions.extend(
        HumanAction(kind, _at(node, prop, tick))
        for label, kind, prop in _STAMPED
        for node in graph.list_nodes(label)
    )
    return tuple(actions)


def _at(node: Node, prop: str, tick: time) -> datetime:
    return instant(node.props.get(prop), tick, label=node.label)


def _acts(graph: GraphStore, audit: Node) -> bool:
    """Whether a CommandAudit records a human trying to change something."""
    families = [
        str(node.props.get("family", ""))
        for node in graph.descendants(audit, max_depth=1, edge_types={"RESULTED_IN"})
        if node.label == "Intent"
    ]
    if families:
        return any(family not in READING_FAMILIES for family in families)
    return audit.props.get("outcome") != _EXPLAIN_CALL


def _off_schedule(graph: GraphStore) -> list[Node]:
    """RunRequests a human placed: a resume, or any id outside the schedule."""
    return [
        node
        for node in graph.list_nodes("RunRequest")
        if node.props.get("resume_from")
        or not str(node.props.get("run_id", "")).startswith(_SCHEDULED)
    ]


def _requested(node: Node, tick: time) -> HumanAction:
    """Time a resume by `resumed_at`: its `requested_at` is its source's copy."""
    if node.props.get("resume_from"):
        return HumanAction("resume", _at(node, "resumed_at", tick))
    return HumanAction("run", _at(node, "requested_at", tick))
