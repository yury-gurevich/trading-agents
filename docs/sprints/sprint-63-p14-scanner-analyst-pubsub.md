# Sprint 63 — P14.4: Scanner + analyst pub/sub dual-mode

**Phase:** P14 — Inter-agent comms re-architecture (ADR-0005)
**Status:** planned
**Branch:** `sprint-63-p14-scanner-analyst-pubsub`
**Effort:** M
**Prerequisite:** S62 shipped (provider pub/sub ready).

---

## Goal

Scanner subscribes to `run.trigger` and drives its own pipeline:

- publishes `data.request.ohlcv` / `data.request.sectors` per ticker
- collects `data.ready.*` events via claim-check
- writes candidates to graph
- publishes `scan.candidates.ready`

Analyst subscribes to `scan.candidates.ready`:

- publishes `data.request.*` per candidate ticker (news, fundamentals, etc.)
- collects ready events
- writes recommendations to graph
- publishes `analysis.recommendations.ready`

**Dual-mode:** both agents retain existing RPC handlers.  Orchestration step functions
unchanged.

**Exit criterion:** publish `run.trigger` → scanner fires → candidates in graph → analyst fires
→ recommendations in graph; claim-check used throughout; CI 100%.

---

## What to build

### Topic map additions

| Producer | Topic | Node label |
| --- | --- | --- |
| Scheduler/Dispatcher | `run.trigger` | — (trigger only, no artifact) |
| Scanner | `scan.candidates.ready` | `ScanResult` |
| Analyst | `analysis.recommendations.ready` | `Recommendation` |

### Run trigger event schema

```python
{"run_id": str, "universe": list[str], "as_of": str}
```

### `agents/scanner/agent.py` changes

In `bind()`, after `super().bind()`:

```python
self.bus.subscribe("run.trigger", self._on_run_trigger)
```

`_on_run_trigger` orchestrates the pub/sub flow using `_collect_ready_events` helper
(see below).

### `agents/analyst/agent.py` changes

In `bind()`, after `super().bind()`:

```python
self.bus.subscribe("scan.candidates.ready", self._on_candidates_ready)
```

### `kernel/claim_check.py` additions (if needed)

A `collect_ready` helper for gathering multiple per-ticker ready events in-process:

```python
def collect_ready(
    bus: MessageBus,
    *,
    request_topic: str,
    ready_topic: str,
    requests: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Publish one request per item, collect synchronous in-process ready events."""
```

In the in-process backend, `publish` fires subscribers synchronously so this is deterministic.

### Tests (`agents/scanner/tests/test_scanner_pubsub.py`

`agents/analyst/tests/test_analyst_pubsub.py`) — new files

Each file tests the pub/sub path end-to-end using `InProcessBus` + `InMemoryGraphStore`:

- trigger → candidates ready event received
- candidates node written to graph with correct ref
- candidates ready → recommendations ready event received
- recommendations node in graph

---

## Non-negotiable guardrails

- Existing RPC tests unchanged.
- The pub/sub handlers use only `claim_check_write` / `claim_check_read`; never
  `bus.request()` from within the event-driven path.
- 100% coverage.

---

## Out of scope

- Removing RPC handlers — S66.
- PM, execution — S64.
