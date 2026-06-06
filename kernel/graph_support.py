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
type Props = Mapping[str, Any]


class _GraphNode(Protocol):
    @property
    def label(self) -> str: ...  # pragma: no cover - protocol declaration only.

    @property
    def key(self) -> str: ...  # pragma: no cover - protocol declaration only.


class _GraphEdge(Protocol):
    @property
    def edge_type(self) -> str: ...  # pragma: no cover - protocol declaration only.


def _frozen_props(props: Props | None) -> Props:
    return MappingProxyType(dict(props or {}))


def _node_key(node: _GraphNode) -> NodeKey:
    return (node.label, node.key)


def _append_props(existing: Props, new_props: Props) -> dict[str, Any]:
    merged = dict(existing)
    for name, value in new_props.items():
        if name in merged and merged[name] != value:
            raise ValueError(f"property {name!r} cannot be overwritten")
        merged[name] = value
    return merged


def _edge_allowed(edge: _GraphEdge, edge_types: set[str] | None) -> bool:
    return edge_types is None or edge.edge_type in edge_types
