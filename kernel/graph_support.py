"""Small shared helpers for graph store implementations.

Agent: kernel
Role: keep graph value-object helper mechanics out of backend modules.
External I/O: none.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from types import MappingProxyType
from typing import Any, Protocol

type NodeKey = tuple[str, str]
type EdgeKey = tuple[NodeKey, NodeKey, str]
type Props = Mapping[str, Any]

# Sentinel prefix marking a property value that was JSON-encoded for Neo4j storage.
# A NUL byte cannot occur in any legitimate identifier, date, or ticker string, so
# it never collides with a genuine native string property.
_JSON_SENTINEL = "\x00json:"


def _prim_kind(value: Any) -> str | None:  # noqa: ANN401 - graph props are JSON-like.
    """Return a Neo4j primitive kind name, or None when *value* is not primitive."""
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        return "str"
    return None


def _neo4j_native(value: Any) -> bool:  # noqa: ANN401 - graph props are JSON-like.
    """True when Neo4j can store *value* as a node property without JSON-encoding.

    Neo4j allows primitives and homogeneous arrays of primitives only; nested maps,
    lists-of-maps, and mixed-type arrays must be encoded (see ``_encode_props``).
    """
    if value is None or _prim_kind(value) is not None:
        return True
    if isinstance(value, list | tuple):
        kinds = {_prim_kind(item) for item in value}
        return None not in kinds and len(kinds) <= 1
    return False


def _encode_props(props: Props) -> dict[str, Any]:
    """JSON-encode property values Neo4j cannot store natively (see ``_neo4j_native``).

    Encoded values are tagged with ``_JSON_SENTINEL`` so ``_decode_props`` restores
    them on read; native primitives and homogeneous primitive arrays pass through.
    """
    return {key: _encode_value(value) for key, value in props.items()}


def _encode_value(value: Any) -> Any:  # noqa: ANN401 - graph props are JSON-like.
    if _neo4j_native(value):
        return value
    return _JSON_SENTINEL + json.dumps(value, sort_keys=True)


def _decode_props(props: Mapping[str, Any]) -> dict[str, Any]:
    """Restore values previously JSON-encoded by ``_encode_props``."""
    return {key: _decode_value(value) for key, value in props.items()}


def _decode_value(value: Any) -> Any:  # noqa: ANN401 - graph props are JSON-like.
    if isinstance(value, str) and value.startswith(_JSON_SENTINEL):
        return json.loads(value[len(_JSON_SENTINEL) :])
    return value


class _GraphNode(Protocol):
    @property
    def label(self) -> str: ...  # pragma: no cover - protocol declaration only.

    @property
    def key(self) -> str: ...  # pragma: no cover - protocol declaration only.


class _GraphEdge(Protocol):
    @property
    def parent(self) -> NodeKey: ...  # pragma: no cover - protocol declaration only.

    @property
    def child(self) -> NodeKey: ...  # pragma: no cover - protocol declaration only.

    @property
    def edge_type(self) -> str: ...  # pragma: no cover - protocol declaration only.


def _frozen_props(props: Props | None) -> Props:
    return MappingProxyType(
        {key: _frozen_value(value) for key, value in dict(props or {}).items()}
    )


def _frozen_value(value: Any) -> Any:  # noqa: ANN401 - graph props are JSON-like.
    if isinstance(value, Mapping):
        return MappingProxyType(
            {key: _frozen_value(nested) for key, nested in value.items()}
        )
    if isinstance(value, list | tuple):
        return tuple(_frozen_value(item) for item in value)
    if isinstance(value, set | frozenset):
        return frozenset(_frozen_value(item) for item in value)
    return value


def _node_key(node: _GraphNode) -> NodeKey:
    return (node.label, node.key)


def _edge_key(edge: _GraphEdge) -> EdgeKey:
    return (edge.parent, edge.child, edge.edge_type)


def _append_props(existing: Props, new_props: Props) -> dict[str, Any]:
    merged = dict(existing)
    for name, value in new_props.items():
        frozen = _frozen_value(value)
        # Freeze both sides before comparing: a value read back from Neo4j is a
        # list, while an incoming sequence freezes to a tuple — normalize so an
        # unchanged re-merge does not read as an illegal overwrite.
        if name in merged and _frozen_value(merged[name]) != frozen:
            raise ValueError(f"property {name!r} cannot be overwritten")
        merged[name] = frozen
    return merged


def _edge_allowed(edge: _GraphEdge, edge_types: set[str] | None) -> bool:
    return edge_types is None or edge.edge_type in edge_types
