"""The held book an S237 export carries: the snapshot and the Position facts read.

Agent: tooling
Role: select the BrokerPositionSnapshot the live PM read, and beside it the Position
      nodes the live analyst and PM read, by the monitor's own post-sync invariant.
External I/O: none (reads the injected GraphStore).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING

from scripts.fidelity_export_helpers import jsonable, parse_dt

if TYPE_CHECKING:
    from datetime import datetime

    from kernel.graph import GraphStore, Node

_SNAPSHOT = "BrokerPositionSnapshot"
# A deactivation marker and the prop naming the snapshot that wrote it (monitor).
_ENDED = (
    ("broker_absent", "broker_absent_snapshot"),
    ("broker_superseded_by", "broker_superseded_snapshot"),
)
# The Position props open_positions / portfolio_from_graph / decided_stop_pct read.
_READ_PROPS = (
    "ticker",
    "quantity",
    "opened_price_cents",
    "broker_market_value_cents",
    "status",
    "provenance",
    "stop_pct",
    "run_id",
    "opened_at",
)
# Read by the live analyst at run time and not rebuildable as of then (DL-238 D4).
HELD_STOP_GAPS = frozenset({"held_stops", "active_broker_stop_refs"})


@dataclass(frozen=True)
class Book:
    """The book one run's stages read, and what of it cannot be rebuilt."""

    snapshot: Node | None
    positions: tuple[dict[str, object], ...]
    gaps: frozenset[str]


def book_for(graph: GraphStore, run_id: str, read_by: datetime | None) -> Book:
    """Return the snapshot the PM read for ``run_id`` and the Positions beside it."""
    snapshot = _snapshot(graph, run_id, read_by)
    if snapshot is None or snapshot.props.get("status") != "fresh":
        return Book(snapshot, (), HELD_STOP_GAPS | {"held_positions"})
    at = parse_dt(snapshot.props.get("created_at"))
    holdings = [
        item for item in snapshot.props.get("holdings", ()) if isinstance(item, Mapping)
    ]
    rows: list[dict[str, object]] = []
    complete = True
    for holding in holdings:
        matches = [
            node
            for node in graph.list_nodes("Position")
            if _equals(node, holding) and not _ended(graph, node, at)
        ]
        if len(matches) == 1:
            rows.append(_position(matches[0]))
        else:
            complete = False
    gaps = set(HELD_STOP_GAPS) if holdings else set()
    if not complete:
        gaps.add("held_positions")
    ordered = tuple(sorted(rows, key=lambda row: str(row["key"])))
    return Book(snapshot, ordered, frozenset(gaps))


def _snapshot(graph: GraphStore, run_id: str, read_by: datetime | None) -> Node | None:
    """The latest snapshot for the run, as `portfolio_from_graph` picks it, pre-read."""
    stamped = [
        (created, node)
        for node in graph.list_nodes(_SNAPSHOT)
        if node.props.get("run_id") == run_id
        and (created := parse_dt(node.props.get("created_at"))) is not None
        and (read_by is None or created <= read_by)
    ]
    if not stamped:
        return None
    return max(stamped, key=lambda item: (item[0], item[1].key))[1]


def _equals(position: Node, holding: Mapping[str, object]) -> bool:
    """After a fresh sync the active Position equals its holding (monitor reconcile)."""
    props = position.props
    return (
        props.get("ticker") == holding.get("ticker")
        and props.get("quantity") == holding.get("quantity")
        and props.get("opened_price_cents") == holding.get("avg_entry_cents")
    )


def _ended(graph: GraphStore, position: Node, at: datetime | None) -> bool:
    """Whether a marker written at or before the snapshot had ended the Position."""
    for flag, snapshot_prop in _ENDED:
        if not position.props.get(flag) and not position.props.get(snapshot_prop):
            continue
        reference = position.props.get(snapshot_prop)
        marker = graph.get_node(_SNAPSHOT, str(reference)) if reference else None
        marked_at = parse_dt(marker.props.get("created_at")) if marker else None
        if marked_at is None or at is None or marked_at <= at:
            return True
    return False


def _position(node: Node) -> dict[str, object]:
    return {
        "key": node.key,
        "props": {
            name: jsonable(node.props[name])
            for name in _READ_PROPS
            if name in node.props
        },
    }
