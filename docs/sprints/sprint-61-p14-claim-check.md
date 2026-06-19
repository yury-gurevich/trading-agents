# Sprint 61 — P14.2: Claim-check helper

**Phase:** P14 — Inter-agent comms re-architecture (ADR-0005)
**Status:** planned
**Branch:** `sprint-61-p14-claim-check`
**Effort:** S–M
**Prerequisite:** S60 shipped (pub/sub on both bus backends).

---

## Goal

Implement the kernel-level claim-check primitive: a producer writes an artifact to the
`GraphStore`, then publishes a tiny `ready:<ref>` event; a consumer receives the event and
reads the artifact back from the graph by reference.  **The data payload never travels on the
bus.**

**Exit criterion:** a produce→consume round-trip on `InMemoryGraphStore`; payload not on bus;
missing-ref → `RuntimeError`; CI gate green at 100%.

---

## Context

ADR-0005 mandates the claim-check pattern because Azure Service Bus caps messages at 256 KB and
market-data payloads are far larger.  The graph is the source of truth; the bus carries only the
`ref` announcement.  This helper is the shared building block all migrating agents (S62+) will use.

---

## What to build

### `kernel/claim_check.py` (new)

Module header: `Agent: kernel / Role: claim-check produce + consume over GraphStore + pub/sub bus.`

```python
from __future__ import annotations

from pydantic import BaseModel, ConfigDict
from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from kernel.bus import MessageBus
    from kernel.graph import GraphStore, Node, Props


class ReadyEvent(BaseModel):
    """Tiny bus payload announcing a graph artifact is ready to consume."""

    model_config = ConfigDict(frozen=True)

    topic: str
    label: str   # Neo4j node label; lets consumers skip knowing the schema
    ref: str     # node key in the GraphStore
    run_id: str | None = None


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
    """Write ``props`` to the graph under ``(label, ref)`` then announce on ``topic``."""
    graph.merge_node(label, ref, props)
    event = ReadyEvent(topic=topic, label=label, ref=ref, run_id=run_id)
    bus.publish(topic, event.model_dump(mode="json"))
    return event


def claim_check_read(graph: GraphStore, event: dict[str, Any]) -> Node:
    """Resolve a ready-event dict → the announced graph node.

    Raises ``RuntimeError`` if the referenced node is absent (signals producer bug).
    """
    ready = ReadyEvent.model_validate(event)
    node = graph.get_node(ready.label, ready.ref)
    if node is None:
        raise RuntimeError(
            f"claim_check_read: no {ready.label!r} node for ref {ready.ref!r}"
        )
    return node
```

### `kernel/__init__.py`

Add `ReadyEvent`, `claim_check_write`, `claim_check_read` to imports and `__all__`.

### `tests/test_claim_check.py` (new)

Module header: `Agent: kernel / Role: verify claim-check produce + consume semantics.`

Tests (7):

| Test name | Verifies |
| --- | --- |
| `test_produce_writes_node_to_graph` | artifact is in the GraphStore after `claim_check_write` |
| `test_produce_publishes_event_to_topic` | the bus subscriber receives the ready event |
| `test_produce_payload_not_on_bus_is_in_graph` | event dict has only `{topic,label,ref,run_id}` not the raw props |
| `test_consume_returns_node_matching_ref` | `claim_check_read` resolves to the written node |
| `test_consume_raises_on_missing_ref` | absent ref → `RuntimeError` |
| `test_produce_consume_round_trip` | full produce→subscribe→consume chain on InMemoryGraphStore |
| `test_ready_event_is_frozen` | `ReadyEvent` mutation raises `ValidationError` |

---

## Non-negotiable guardrails

- `kernel/claim_check.py` < 80 lines.
- `ReadyEvent` uses Pydantic (`model_config = ConfigDict(frozen=True)`), matching the
  project's DTO style.
- `claim_check_write` is side-effect only re. bus: **it does not return the event on the bus**;
  subscribers receive it asynchronously.
- `claim_check_read` raises (not returns `None`) on a missing ref — makes bugs loud.
- 100% coverage.

---

## Acceptance criteria

- [ ] `from kernel import ReadyEvent, claim_check_write, claim_check_read` works.
- [ ] Round-trip: write → subscribe → publish → read returns identical props.
- [ ] Missing ref → `RuntimeError`.
- [ ] `ReadyEvent` frozen (cannot mutate after construction).
- [ ] `pytest` → 100.00% coverage; all tests pass.

---

## Out of scope

- Agent migration — S62+.
- Multiple-artifact fanout helpers — add when a consumer needs them.
- Azure Service Bus integration — S67.
