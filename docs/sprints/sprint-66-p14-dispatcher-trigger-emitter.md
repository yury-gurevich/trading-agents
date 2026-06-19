# Sprint 66 — P14.7: Dispatcher → trigger-emitter + watchdog

**Phase:** P14 — Inter-agent comms re-architecture (ADR-0005)
**Status:** planned
**Branch:** `sprint-66-p14-dispatcher-trigger-emitter`
**Effort:** M
**Prerequisite:** S65 shipped (all agents dual-mode; full pub/sub pipeline proven).

---

## Goal

Replace the dispatcher's step-sequencing loop with a single trigger-emit: the dispatcher
publishes `run.trigger`; agents choreograph themselves; the dispatcher subscribes to
`report.snapshot.ready` and `monitor.decisions.ready` to detect completion/failure.

Dead-letter / timeout / retry surfaced via the supervisor watchdog.

After this sprint the `step_*` functions in `orchestration/steps.py` and the explicit
`execute_run` call sequence are **removed**.  The daily loop is fully event-driven on the
in-process bus.

**Exit criterion:** P4 daily loop runs event-driven end-to-end on the in-process bus; the
old `step_scan` / `step_analyze` / ... sequence is gone; supervisor records run lineage;
CI 100%.

---

## What to build

### `orchestration/dispatcher.py` rewrite

```python
def execute_run(self, trigger: RunTrigger) -> RunResult:
    active = outcome.active_trigger(trigger, self.settings.universe)
    result_box: list[RunResult] = []

    def _on_snapshot_ready(event: dict[str, Any]) -> None:
        # read snapshot from graph, build RunResult
        ...

    self.bus.subscribe("report.snapshot.ready", _on_snapshot_ready)
    self.bus.publish("run.trigger", {"run_id": active.run_id, ...})
    # In-process: the entire chain runs synchronously before we reach here
    return result_box[0] if result_box else self._timed_out(active.run_id)
```

### Remove `orchestration/steps.py`

All `step_*` functions removed.  Tests that use them are replaced with end-to-end
pub/sub pipeline tests.

### Supervisor watchdog

`orchestration/supervisor.py` gains a `watch_run(run_id, timeout_s)` method that raises
a `RunTimeout` fault if `report.snapshot.ready` doesn't arrive in time.

### Tests

- `orchestration/tests/test_p14_pubsub_loop.py` — end-to-end: publish `run.trigger` →
  verify `report.snapshot.ready` arrives; RunResult has correct steps.
- `test_p4_daily_loop.py` updated (or removed) to use the new trigger-emit pattern.
- `test_p4_celery_parity.py` updated to verify both backends produce the same result.

### `orchestration/lineage.py` update

Message lineage recording adapts to `run.trigger` as the lineage root (was the first RPC
request).

---

## Non-negotiable guardrails

- RPC removed from all inter-agent data paths after this sprint; operator/human sync
  path (operator agent → `bus.request()`) is the only remaining RPC use.
- 100% coverage — any dead `step_*` code removed (not `# pragma: no cover`).
- Supervisor records `DispatchRunRecord` with the same shape as before.

---

## Out of scope

- Azure Service Bus backend — S67.
- Forecaster / researcher pub/sub migration (those are advisory; they get their own
  subsequent sprint if needed).
