"""Projection helpers for the S237 fidelity export.

Agent: tooling
Role: follow live lineage edges and turn graph nodes into JSON-safe blocks.
External I/O: none (reads the injected GraphStore).
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import UTC, date, datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kernel.graph import GraphStore, Node

_LINKED_FROM = "linked_from_key"


def node_props(node: Node | None) -> dict[str, object]:
    """Return a node's props as ordinary JSON-safe containers."""
    if node is None:
        return {}
    props = jsonable(node.props)
    return props if isinstance(props, dict) else {}


def node_block(node: Node | None, *names: str) -> dict[str, object]:
    """Return a node's key and the named props, or an empty block."""
    if node is None:
        return {}
    props = node_props(node)
    return {"key": node.key, **{name: props.get(name) for name in names}}


def nodes_to_props(nodes: Iterable[Node]) -> list[dict[str, object]]:
    """Return node props in key order, for deterministic JSON."""
    return [node_props(node) for node in sorted(nodes, key=lambda item: item.key)]


def child(graph: GraphStore, node: Node | None, edge: str, label: str) -> Node | None:
    """Return the child of ``node`` reached over ``edge`` with ``label``."""
    if node is None:
        return None
    return next(
        (
            item
            for item in graph.descendants(node, max_depth=1, edge_types={edge})
            if item.label == label
        ),
        None,
    )


def resolved(graph: GraphStore, node: Node | None) -> Node | None:
    """Follow a resume clone's ``linked_from_key`` to the output it copies."""
    if node is None:
        return None
    source = node.props.get(_LINKED_FROM)
    if source:
        return graph.get_node(node.label, str(source)) or node
    return node


def is_linked(node: Node | None) -> bool:
    """Return whether a stage node is a resume clone."""
    return node is not None and bool(node.props.get(_LINKED_FROM))


def deploy_for(graph: GraphStore, scan: Node | None) -> dict[str, object]:
    """Return the DeployRecord in force when the scan ran, or nothing at all."""
    scan_at = parse_dt(scan.props.get("created_at")) if scan else None
    if scan_at is None:
        return {}
    records = [
        (deployed_at, node)
        for node in graph.list_nodes("DeployRecord")
        if (deployed_at := parse_dt(node.props.get("deployed_at"))) is not None
        and deployed_at <= scan_at
    ]
    if not records:
        return {}
    return node_props(max(records, key=lambda item: (item[0], item[1].key))[1])


def regime_for(graph: GraphStore, market: Node | None) -> dict[str, object]:
    """Return the RegimeContext snapshot the stages read for this market run."""
    if market is None:
        return {}
    run_id = str(market.props.get("run_id", ""))
    snapshot = node_props(graph.get_node("RegimeContext", f"regime-context:{run_id}"))
    value = snapshot.get("snapshot")
    return value if isinstance(value, dict) else {}


def parse_dt(value: object) -> datetime | None:
    """Parse an ISO timestamp prop; a naive value reads as UTC."""
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)


def jsonable(value: object) -> object:
    """Convert frozen graph props into JSON-safe containers."""
    if isinstance(value, Mapping):
        return {str(key): jsonable(item) for key, item in value.items()}
    if isinstance(value, tuple | list | frozenset | set):
        items = [jsonable(item) for item in value]
        return sorted(items, key=str) if isinstance(value, frozenset | set) else items
    if isinstance(value, date | datetime):
        return value.isoformat()
    return value
