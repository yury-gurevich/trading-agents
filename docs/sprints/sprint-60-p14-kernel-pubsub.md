# Sprint 60 — P14.1: Kernel pub/sub primitive

**Phase:** P14 — Inter-agent comms re-architecture (ADR-0005)
**Status:** active
**Branch:** `sprint-60-p14-kernel-pubsub`
**Effort:** S
**Prerequisite:** S59 shipped; S60 is the first in the 8-sprint P14 sequence.

---

## Goal

Extend the `MessageBus` protocol with fire-and-forget pub/sub: `publish(topic, event)` and
`subscribe(topic, handler)`.  Both `InProcessBus` and `CeleryBus` gain synchronous in-process
fan-out implementations.  Request/response RPC is **unchanged** — it remains for the
operator/human sync path.  No agents are touched.

**Exit criterion:** an echo publish→subscribe round-trip works on both bus backends; fan-out to
N subscribers is correct; CI gate green at 100%.

---

## Context

ADR-0005 adopted event-driven pub/sub + claim-check over Azure Service Bus.  The in-process
bus is the infra-free proving ground; the Azure backend lands in S67 (P14.8).  Every subsequent
P14 sprint builds on the primitives introduced here.

---

## What to build

### `kernel/bus.py`

Add at module level:

```python
EventHandler = Callable[[dict[str, Any]], None]
```

Extend `MessageBus` Protocol:

```python
def subscribe(self, topic: str, handler: EventHandler) -> None:
    """Register a handler to receive all events published to ``topic``."""
    ...  # pragma: no cover

def publish(self, topic: str, event: dict[str, Any]) -> None:
    """Deliver ``event`` synchronously to every subscriber on ``topic``."""
    ...  # pragma: no cover
```

Extend `InProcessBus`:

```python
# in __init__:
self._subscribers: dict[str, list[EventHandler]] = {}

def subscribe(self, topic: str, handler: EventHandler) -> None:
    self._subscribers.setdefault(topic, []).append(handler)

def publish(self, topic: str, event: dict[str, Any]) -> None:
    for handler in self._subscribers.get(topic, []):
        handler(event)
```

### `kernel/bus_celery.py`

Same fan-out implementation on `CeleryBus` (in-process for now; S67 replaces this
with Azure Service Bus topics).

```python
# in __init__:
self._subscribers: dict[str, list[EventHandler]] = {}

def subscribe(self, topic: str, handler: EventHandler) -> None:
    self._subscribers.setdefault(topic, []).append(handler)

def publish(self, topic: str, event: dict[str, Any]) -> None:
    for handler in self._subscribers.get(topic, []):
        handler(event)
```

Import `EventHandler` from `kernel.bus`.

### `kernel/__init__.py`

Add `EventHandler` to imports and `__all__`.

### `tests/test_bus_pubsub.py` (new)

Module header: `Agent: kernel / Role: verify in-process and Celery bus pub/sub fan-out.`

Tests (8):

| Test name | Verifies |
| --- | --- |
| `test_in_process_subscribe_receives_published_event` | single subscriber gets event |
| `test_in_process_fan_out_delivers_to_all_subscribers` | two subscribers on same topic both fire |
| `test_in_process_publish_to_unknown_topic_is_silent` | no-op, no error |
| `test_in_process_separate_topics_do_not_cross` | topic A event not delivered to topic B subscriber |
| `test_in_process_multiple_publishes_deliver_in_order` | three publishes arrive in order |
| `test_celery_bus_subscribe_receives_published_event` | CeleryBus fan-out works |
| `test_celery_bus_fan_out_delivers_to_all_subscribers` | two CeleryBus subscribers |
| `test_celery_bus_publish_to_unknown_topic_is_silent` | CeleryBus no-op, no error |

---

## Non-negotiable guardrails

- `EventHandler` type alias exported from `kernel/` and `kernel/__init__.py`.
- `MessageBus` Protocol stubs marked `# pragma: no cover - protocol declaration only.`
- All new `InProcessBus` and `CeleryBus` methods covered by the test file above.
- No agent file touched.
- `make ci` green at 100.00% before commit.

---

## Acceptance criteria

- [ ] `from kernel import EventHandler` works.
- [ ] `bus.subscribe("t", fn); bus.publish("t", {})` → `fn` called exactly once.
- [ ] Two subscribers → both called on publish.
- [ ] `bus.publish("ghost", {})` → no exception.
- [ ] `mypy --strict` sees `InProcessBus` and `CeleryBus` as structural subtypes of the
      extended `MessageBus` Protocol.
- [ ] `pytest` → 100.00% coverage; all tests pass.

---

## Out of scope

- Typed event envelopes (`ReadyEvent`) — that is S61.
- Claim-check helpers — S61.
- Agent migration — S62+.
- Azure Service Bus backend — S67.
