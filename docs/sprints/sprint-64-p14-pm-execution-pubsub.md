# Sprint 64 — P14.5: Portfolio manager + execution pub/sub dual-mode

**Phase:** P14 — Inter-agent comms re-architecture (ADR-0005)
**Status:** MERGED — `e59c6a53` on `main` (feat(p14): event-driven pub/sub re-architecture + Azure Service Bus ba) (item 22 review, 2026-09-23); the line read: planned
**Branch:** `sprint-64-p14-pm-execution-pubsub`
**Effort:** M
**Prerequisite:** S63 shipped.

---

## Goal

Portfolio manager subscribes to `analysis.recommendations.ready`, evaluates, writes order
intents to graph, publishes `portfolio.orders.ready`.

Execution subscribes to `portfolio.orders.ready`, submits to broker, writes fills to graph,
publishes `execution.fills.ready`.

Dual-mode; RPC handlers retained.

**Exit criterion:** recommend→size→submit→fill chain flows on pub/sub bus; claim-check
throughout; CI 100%.

---

## Topic map additions

| Producer | Topic | Node label |
| --- | --- | --- |
| Portfolio manager | `portfolio.orders.ready` | `OrderIntent` |
| Execution | `execution.fills.ready` | `Fill` |

---

## What to build

### `agents/portfolio_manager/agent.py`

`bind()` → `super().bind()` then:

```python
self.bus.subscribe("analysis.recommendations.ready", self._on_recommendations_ready)
```

### `agents/execution/agent.py`

```python
self.bus.subscribe("portfolio.orders.ready", self._on_orders_ready)
```

### Tests

- `agents/portfolio_manager/tests/test_pm_pubsub.py`
- `agents/execution/tests/test_execution_pubsub.py`

Each: trigger the upstream ready event, verify the downstream ready event and graph node.

---

## Out of scope

- Monitor, reporter — S65.
- RPC removal — S66.
