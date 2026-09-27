"""Helper functions for S237 fidelity export JSON projection.

Agent: tooling
Role: normalize graph nodes and export-adjacent evidence into JSON-safe shapes.
External I/O: none.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import UTC, date, datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kernel.graph import GraphStore, Node


def node_props(node: Node | None) -> dict[str, object]:
    """Return a graph node's props as ordinary JSON-safe containers."""
    return jsonable(node.props) if node else {}


def node_payload(label: str, node: Node | None, payload_key: str) -> dict[str, object]:
    """Return a keyed graph payload block."""
    return {
        "label": label,
        "key": node.key if node else None,
        payload_key: jsonable(node.props.get(payload_key)) if node else None,
    }


def nodes_to_props(nodes: Iterable[Node]) -> list[dict[str, object]]:
    """Return sorted node props for deterministic JSON."""
    return [node_props(node) for node in sorted(nodes, key=lambda item: item.key)]


def held_stop_inputs(graph: GraphStore, book: Node | None) -> dict[str, object]:
    """Return held tickers and any visible broker-stop facts."""
    holdings = node_props(book).get("holdings", ()) if book else ()
    held = [str(item.get("ticker")) for item in holdings if isinstance(item, Mapping)]
    stops = [
        node_props(node)
        for node in graph.list_nodes("BrokerStopOrder")
        if str(node.props.get("ticker", "")) in set(held)
    ]
    return {"held_tickers": sorted(held), "broker_stop_orders": stops}


def fills_for_pm(graph: GraphStore, pm: Node | None) -> list[dict[str, object]]:
    """Return Fill nodes linked to a PM run by common live graph conventions."""
    if pm is None:
        return []
    order_keys = {
        node.key for node in graph.ancestors(pm, max_depth=1, edge_types={"EMITTED_BY"})
    }
    return [
        node_props(node)
        for node in graph.list_nodes("Fill")
        if str(node.props.get("order_ref", "")) in order_keys
        or str(node.props.get("pm_run_id", "")) == pm.key
    ]


def not_persisted_fields(market: Node | None, book: Node | None) -> set[str]:
    """Name live inputs the export cannot faithfully reconstruct."""
    missing: set[str] = set()
    snapshot = node_props(market).get("snapshot", {}) if market else {}
    if isinstance(snapshot, Mapping) and not snapshot.get("benchmark"):
        missing.add("benchmark")
    holdings = node_props(book).get("holdings", ()) if book else ()
    if holdings:
        missing.add("held_stop_refs")
    return missing


def parse_dt(value: object) -> datetime | None:
    """Parse an ISO datetime from a graph prop."""
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed


def jsonable(value: object) -> object:
    """Convert frozen graph props into JSON-safe containers."""
    if isinstance(value, Mapping):
        return {str(key): jsonable(item) for key, item in value.items()}
    if isinstance(value, tuple | list):
        return [jsonable(item) for item in value]
    if isinstance(value, date | datetime):
        return value.isoformat()
    return value
