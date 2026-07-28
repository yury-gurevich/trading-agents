"""Fill attempt-chain helpers for append-safe execution writes.

Agent: execution
Role: separate broker idempotency keys from immutable graph Fill node keys.
External I/O: none.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Mapping

    from kernel import GraphStore, Node

ATTEMPT_SEPARATOR = "#"
BASE_ATTEMPT_ORDINAL = 0
BROKER_IDEMPOTENCY_PROP = "broker_idempotency_key"
ATTEMPT_ORDINAL_PROP = "attempt_ordinal"


@dataclass(frozen=True)
class FillAttempt:
    """The graph key and props for one append-safe Fill attempt."""

    key: str
    ordinal: int
    props: dict[str, object]


def select_fill_attempt(
    graph: GraphStore,
    broker_idempotency_key: str,
    props: dict[str, object],
    *,
    force_new: bool = False,
) -> FillAttempt:
    """Return an existing compatible attempt, or the first free ordinal."""
    ordinal = BASE_ATTEMPT_ORDINAL
    while True:
        key = fill_attempt_key(broker_idempotency_key, ordinal)
        attempt_props = _with_attempt_props(props, broker_idempotency_key, ordinal)
        current = graph.get_node("Fill", key)
        if current is None or (
            not force_new and _props_compatible(current.props, attempt_props)
        ):
            return FillAttempt(key=key, ordinal=ordinal, props=attempt_props)
        ordinal += 1


def latest_fill_attempt(graph: GraphStore, broker_idempotency_key: str) -> Node | None:
    """Return the latest Fill node for one broker idempotency key."""
    chain = fill_attempt_chain(graph, broker_idempotency_key)
    return None if not chain else chain[-1]


def fill_attempt_chain(
    graph: GraphStore, broker_idempotency_key: str
) -> tuple[Node, ...]:
    """Return Fill nodes for one broker key, ordered by attempt ordinal."""
    nodes = [
        node
        for node in graph.list_nodes("Fill")
        if _belongs_to_chain(node, broker_idempotency_key)
    ]
    return tuple(
        sorted(nodes, key=lambda node: attempt_ordinal(node, broker_idempotency_key))
    )


def fill_attempt_key(broker_idempotency_key: str, ordinal: int) -> str:
    """Return the graph key for an attempt ordinal."""
    if ordinal == BASE_ATTEMPT_ORDINAL:
        return broker_idempotency_key
    return f"{broker_idempotency_key}{ATTEMPT_SEPARATOR}{ordinal}"


def attempt_ordinal(node: Node, broker_idempotency_key: str) -> int:
    """Recover a Fill node's attempt ordinal from props or key suffix."""
    value = node.props.get(ATTEMPT_ORDINAL_PROP)
    if isinstance(value, int):
        return value
    suffix = node.key.removeprefix(broker_idempotency_key)
    if suffix.startswith(ATTEMPT_SEPARATOR) and suffix[1:].isdigit():
        return int(suffix[1:])
    return BASE_ATTEMPT_ORDINAL


def broker_idempotency_key(node: Node) -> str:
    """Return the broker idempotency key that owns a Fill node."""
    value = node.props.get(BROKER_IDEMPOTENCY_PROP)
    if isinstance(value, str) and value:
        return value
    return node.key.split(ATTEMPT_SEPARATOR, 1)[0]


def _with_attempt_props(
    props: dict[str, object], broker_idempotency_key: str, ordinal: int
) -> dict[str, object]:
    attempt_props = dict(props)
    attempt_props[BROKER_IDEMPOTENCY_PROP] = broker_idempotency_key
    attempt_props[ATTEMPT_ORDINAL_PROP] = ordinal
    return attempt_props


def _props_compatible(
    existing: Mapping[str, Any], new_props: dict[str, object]
) -> bool:
    for name, value in new_props.items():
        if name in existing and existing[name] != value:
            return False
    return True


def _belongs_to_chain(node: Node, broker_idempotency_key: str) -> bool:
    if node.props.get(BROKER_IDEMPOTENCY_PROP) == broker_idempotency_key:
        return True
    return node.key == broker_idempotency_key or _has_ordinal_suffix(
        node.key, broker_idempotency_key
    )


def _has_ordinal_suffix(key: str, broker_idempotency_key: str) -> bool:
    suffix = key.removeprefix(broker_idempotency_key)
    return suffix.startswith(ATTEMPT_SEPARATOR) and suffix[1:].isdigit()
