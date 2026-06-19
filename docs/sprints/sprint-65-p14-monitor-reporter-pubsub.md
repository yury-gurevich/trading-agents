# Sprint 65 — P14.6: Monitor + reporter pub/sub dual-mode

**Phase:** P14 — Inter-agent comms re-architecture (ADR-0005)
**Status:** planned
**Branch:** `sprint-65-p14-monitor-reporter-pubsub`
**Effort:** M
**Prerequisite:** S64 shipped.

---

## Goal

Monitor subscribes to `execution.fills.ready`, evaluates open positions, writes close
decisions to graph, publishes `monitor.decisions.ready`.

Reporter subscribes to both `run.trigger` (to know the run_id) and `monitor.decisions.ready`
(to gather completed data), produces a snapshot, writes to graph, publishes
`report.snapshot.ready`.

After this sprint the full agent pipeline — trigger → scan → analyze → pm → execute → monitor
→ report — is wired on the pub/sub bus end-to-end (dual-mode).

**Exit criterion:** full pub/sub chain produces a `report.snapshot.ready` event with the
snapshot ref in graph; CI 100%.

---

## Topic map additions

| Producer | Topic | Node label |
| --- | --- | --- |
| Monitor | `monitor.decisions.ready` | `CloseDecision` |
| Reporter | `report.snapshot.ready` | `RunSnapshot` |

---

## What to build

### `agents/monitor/agent.py`

```python
self.bus.subscribe("execution.fills.ready", self._on_fills_ready)
```

### `agents/reporter/agent.py`

Reporter needs state across two events (`run.trigger` for run_id, then
`monitor.decisions.ready` to produce the report):

```python
self.bus.subscribe("run.trigger", self._on_run_trigger)
self.bus.subscribe("monitor.decisions.ready", self._on_decisions_ready)
```

In the in-process synchronous bus, `run.trigger` fires the entire chain before
`monitor.decisions.ready` arrives, so state accumulation is deterministic.

### Tests

- `agents/monitor/tests/test_monitor_pubsub.py`
- `agents/reporter/tests/test_reporter_pubsub.py`

End-to-end pub/sub pipeline smoke test in reporter tests: fire `run.trigger` → verify
`report.snapshot.ready` arrives and snapshot is in graph.

---

## Out of scope

- Removing RPC / step-sequencing — S66.
- Azure backend — S67.
