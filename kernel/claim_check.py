"""Claim-check helpers for the kernel pub/sub layer.

Agent: kernel
Role: write graph artifacts and publish ready events; resolve ready events back to
      graph nodes. Data payloads travel in the GraphStore; the bus carries only the
      small ref-announcement (required by the 256 KB Azure Service Bus cap).
External I/O: none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ConfigDict

if TYPE_CHECKING:
    from kernel.bus import MessageBus
    from kernel.graph import GraphStore, Node, Props


class ReadyEvent(BaseModel):
    """Tiny bus payload announcing that a graph artifact is ready to consume."""

    model_config = ConfigDict(frozen=True)

    topic: str
    """The pub/sub topic this event was published on."""

    label: str
    """Neo4j node label; lets consumers look up the node without schema knowledge."""

    ref: str
    """Node key in the GraphStore — use ``claim_check_read`` to resolve it."""

    run_id: str | None = None
    """Optional run correlation id; threads the event back to a dispatch run."""


def claim_check_write(
    bus: MessageBus,
    graph: GraphStore,
    *,
    topic: str,
    label: str,
    ref: str,
    props: Props,
    run_id: str | None = None,
) -> ReadyEvent:
    """Write ``props`` to the graph under ``(label, ref)`` then announce on ``topic``.

    The props are stored in the graph; the bus receives only the small
    ``ReadyEvent`` (topic, label, ref, run_id).  Returns the published event.
    """
    graph.merge_node(label, ref, props)
    event = ReadyEvent(topic=topic, label=label, ref=ref, run_id=run_id)
    bus.publish(topic, event.model_dump(mode="json"))
    return event


def claim_check_read(graph: GraphStore, event: dict[str, Any]) -> Node:
    """Resolve a ready-event dict to the announced graph node.

    Raises ``RuntimeError`` if the referenced node is absent — that indicates a
    producer bug (announce before write, or wrong ref).
    """
    ready = ReadyEvent.model_validate(event)
    node = graph.get_node(ready.label, ready.ref)
    if node is None:
        raise RuntimeError(
            f"claim_check_read: no {ready.label!r} node for ref {ready.ref!r}"
        )
    return node
