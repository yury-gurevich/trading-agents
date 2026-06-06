"""Cypher-safe helpers for the Neo4j graph backend.

Agent: kernel
Role: validate dynamic graph identifiers and translate Neo4j records to nodes.
External I/O: none.
"""

from __future__ import annotations

import re
from collections.abc import Mapping  # noqa: TC003 - helper annotations stay simple.
from typing import Any

from kernel.graph import Node
from kernel.graph_support import Props, _append_props

_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _identifier(value: str) -> str:
    if _IDENTIFIER.fullmatch(value) is None:
        raise ValueError(f"unsafe graph identifier {value!r}")
    return f"`{value}`"


def _relationship_pattern(edge_types: set[str] | None, max_depth: int) -> str:
    if edge_types is None:
        return f"[*1..{max_depth}]"
    rel_types = "|".join(_identifier(edge_type) for edge_type in sorted(edge_types))
    return f"[:{rel_types}*1..{max_depth}]"


def _stored_props(props: Mapping[str, Any]) -> dict[str, Any]:
    out = dict(props)
    out.pop("key", None)
    out.pop("schema_version", None)
    return out


def _new_props(existing: Mapping[str, Any], incoming: Props) -> dict[str, Any]:
    merged = _append_props(existing, incoming)
    return {key: value for key, value in merged.items() if key not in existing}


def _node_from_props(label: str, key: str, props: Mapping[str, Any]) -> Node:
    stored = dict(props)
    schema_version = int(stored.pop("schema_version"))
    stored.pop("key", None)
    return Node(label=label, key=key, props=stored, schema_version=schema_version)
