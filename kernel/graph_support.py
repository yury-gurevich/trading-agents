"""Small shared helpers for graph store implementations.

Agent: kernel
Role: keep graph value-object helper mechanics out of backend modules.
External I/O: none.
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import Any, Protocol

type NodeKey = tuple[str, str]
type EdgeKey = tuple[NodeKey, NodeKey, str]
type Props = Mapping[str, Any]


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
        # Freeze both sides before comparing so JSON-backed lists and incoming
        # sequences normalize before append-only conflict detection.
        if name in merged and _frozen_value(merged[name]) != frozen:
            raise ValueError(f"property {name!r} cannot be overwritten")
        merged[name] = frozen
    return merged


def _edge_allowed(edge: _GraphEdge, edge_types: set[str] | None) -> bool:
    return edge_types is None or edge.edge_type in edge_types
