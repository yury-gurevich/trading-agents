# Sprint 15 — Scheduler + supervisor message lineage (P4 exit)

**Status:** planned · **Branch:** `sprint-15-supervisor` · **Build phase:** P4 (orchestration) · **Effort: M**

## Goal

Complete P4's exit criterion: "the daily loop runs on the distributed bus, event-driven,
with the supervisor recording message lineage." Three deliverables: (1) fix a one-line
behavioral bug in `step_check_positions`; (2) implement the `RunScheduler` — the component
that generates `RunTrigger`s and keeps agents idle until messaged; (3) implement a minimal
`SupervisorAgent` with `report_fault` + a new `record_dispatch_run` capability — writing
`Message` and `Fault` nodes so every dispatcher run has a traceable audit record in the graph.

**P4 exit criterion met when** the P4 parity tests (`test_p4_daily_loop` + `test_p4_celery_parity`)
assert that `Message` nodes appear in the graph after a completed run, AND the supervisor
boundary meta-test is green.

## Why (context)

- Read first: `docs/sprints/README.md` (guardrails + gate); `docs/architecture.md` (layers,
  the one rule); `.importlinter`; `docs/build-plan.md` P4 exit description; `contracts/supervisor.py`
  (the full contract — we add one P4 capability, keep P5 capabilities as stubs);
  `orchestration/dispatcher.py` (140 lines — max budget for this sprint is 150 after changes);
  `orchestration/steps.py` (the all-hold bug at line 98); `orchestration/bindings.py`
  (bind the supervisor here); `kernel/errors.py` (`AgentFault`, `fault_boundary`);
  `contracts/common.py` (`_Frozen`, `Provenance`).
- The supervisor contract already exists (`contracts/supervisor.py`). For P4 we add one new
  lightweight capability (`record_dispatch_run`) that records message lineage without needing
  the full P5 routing/gate machinery. The P5 capabilities (`dispatch_intent`, `system_status`,
  `flag_for_human`) are NOT implemented — do not stub them.
- The supervisor `owns_graph = ("Message", "Agent", "Flag", "Fault")`. Only `Message` and
  `Fault` are written this sprint. `Agent` and `Flag` nodes are P5.

## Key design constraints (do not break)

- **One supervisor bus call per run, not per step.** The dispatcher collects its `CollectingFaultSink`
  at the end of `execute_run` and sends ONE `supervisor.record_dispatch_run(DispatchRunRecord)` call
  with all steps attempted + all faults. The supervisor writes N `Message` nodes (one per step).
  This keeps `dispatcher.py` ≤ 150 lines — no per-step calls in the sequencing body.
- **The one rule.** `agents/supervisor/` imports `kernel` + `contracts` only. It never imports
  another agent. It reads and writes the graph.
- **Scheduler does not own the event loop.** `RunScheduler` is a plain factory — given a date (or
  defaulting to today), it returns a `RunTrigger`. The actual cron/event-loop that calls the
  scheduler is deployment infra and is not built this sprint. The key test is "idle": constructing
  a `Dispatcher` and NOT calling `execute_run` leaves the graph empty.
- **P4 contract change is additive.** Adding `record_dispatch_run` to `contracts/supervisor.py`
  is the only contract change this sprint. Do NOT modify any other contract.
- **`step_check_positions` fix is a one-liner.** Change the guard on `steps.py:98` so that an
  empty `CloseDecisionSet.decisions` is NOT treated as a failure — only `None` (actual fault)
  returns `None`. An all-hold run is a valid outcome.
- **Small files, headers, < 200 lines; no magic numbers.**

## Deliverables

### 1. Bug fix — `orchestration/steps.py` line 98

```python
# Before (wrong — treats all-hold as failure):
return result if result is not None and result.decisions else None
# After (correct — only faults return None):
return result
```

One line change. All existing tests must still pass.

### 2. Contract update — `contracts/supervisor.py`

Add `DispatchRunRecord` payload and `record_dispatch_run` capability:

```python
class DispatchRunRecord(_Frozen):
    run_id: str
    steps_attempted: tuple[str, ...]  # e.g. ("scan", "analyze", "evaluate", "submit", "check_positions", "report", "narrative")
    completed: bool
    reason: str | None = None
    faults: tuple[AgentFault, ...] = ()
```

Add to `CONTRACT.consumes`:

```python
Capability(
    "record_dispatch_run",
    "Record per-step message lineage and any faults for one completed or partial run.",
    request=DispatchRunRecord,
    response=DispatchResult,
),
```

Keep existing `dispatch_intent`, `system_status`, `flag_for_human`, `report_fault` capabilities
in the contract exactly as-is — the supervisor agent just won't handle them yet.

### 3. Supervisor agent — `agents/supervisor/`

**`agents/supervisor/store.py`**:

- `write_message(graph, run_id, step_name, status) -> Node`:
  `merge_node("Message", f"{run_id}:{step_name}", {"run_id": run_id, "step": step_name, "status": status, "created_at": ...})`
- `write_fault(graph, fault) -> Node`:
  `merge_node("Fault", f"{fault.run_id}:{fault.agent}:{fault.module}", {"agent": ..., "module": ..., "capability": ..., "message": str(fault.exc)[:500]})`

**`agents/supervisor/agent.py`** — `SupervisorAgent(AgentBase)` (inject `graph`, `settings`,
`sink`), ≤ 150 lines:

- `record_dispatch_run(DispatchRunRecord) -> DispatchResult`: iterate `steps_attempted`,
  call `write_message` for each; call `write_fault` for each fault in `record.faults`;
  return `DispatchResult(accepted=True, provenance=...)`.
- `report_fault(AgentFault) -> DispatchResult`: write one `Fault` node; return
  `DispatchResult(accepted=True, provenance=...)`.
- Wrap both handlers in `fault_boundary(reraise=False)`.
- Do NOT implement `dispatch_intent`, `system_status`, or `flag_for_human`. If the bus receives
  those, the `AgentBase` default unknown-capability error response is correct.

**`agents/supervisor/settings.py`** — `SupervisorSettings(AgentSettings)`,
`env_prefix="SUPERVISOR_"`. One justified tunable: `max_fault_message_chars` (default 500,
why: bound the Fault node body to keep graph props scannable; cap at 2000 for long traces).

**`agents/supervisor/mission.md`** — minimal: purpose (record message lineage, act on faults),
owns_graph labels (`Message`, `Fault` in P4; `Agent`, `Flag` in P5), what it does NOT do (trade
decisions, capability routing — those are P5).

**`agents/supervisor/__init__.py`** — export `SupervisorAgent`.

Update `contracts/supervisor.py` `owns_graph` check: boundary meta-test already uses this field
to verify single-writer-per-label. Confirm `Message` and `Fault` labels are now claimed by
supervisor (they were previously unclaimed). If `scripts/boundary_meta_test.py` or similar
enforces this, ensure it passes.

### 4. Dispatcher update — `orchestration/dispatcher.py`

Add a `_record_run` helper (keeps `execute_run` body clean) and call it as the last step:

```python
def _record_run(self, result: RunResult, steps: tuple[str, ...]) -> None:
    """Send one record_dispatch_run to the supervisor after execute_run."""
    record = DispatchRunRecord(
        run_id=result.run_id,
        steps_attempted=steps,
        completed=result.completed,
        reason=result.reason,
        faults=tuple(getattr(self.sink, "faults", ())),
    )
    step_record_dispatch_run(self.bus, record, self.sink)
```

Track steps attempted as a local list inside `execute_run`, appending each step name after
the bus call returns (whether or not it returned `None`). Call `_record_run` before every
`return` in `execute_run` (both `_stopped` paths and the success path). Keep `dispatcher.py`
≤ 150 lines — if needed, move `_position_ids_for_run` to `steps.py` or a helper module.

Add to `orchestration/steps.py`:

```python
def step_record_dispatch_run(
    bus: MessageBus, record: DispatchRunRecord, sink: FaultSink | None = None
) -> DispatchResult | None:
    """Send supervisor.record_dispatch_run; return None on fault."""
    ...
```

### 5. Bindings update — `orchestration/bindings.py`

Add `SupervisorAgent` import and binding to `bind_paper_loop_agents`. It becomes the 8th agent.
Inject `SupervisorSettings` (or default). The supervisor needs `graph` and `sink`.

### 6. Scheduler — `orchestration/scheduler.py`

```python
class RunScheduler:
    def __init__(self, *, settings: OrchestratorSettings | None = None):
        self.settings = settings or OrchestratorSettings()
    def make_trigger(self, run_id: str, as_of: date | None = None) -> RunTrigger:
        return RunTrigger(
            run_id=run_id,
            universe=self.settings.universe,
            as_of=as_of or date.today(),
        )
```

Add to `orchestration/__init__.py` exports: `RunScheduler`.

### 7. Tests

**`agents/supervisor/tests/test_supervisor_agent.py`** — infra-free:

- `record_dispatch_run` with 3 steps writes 3 `Message` nodes in graph.
- `record_dispatch_run` with faults writes `Fault` nodes.
- `report_fault` writes one `Fault` node.
- Unknown capability returns an error response (no crash).
- Boundary meta-test: supervisor's `owns_graph` labels (`Message`, `Fault`) claimed by
  exactly one agent.

**`orchestration/tests/test_p4_scheduler.py`**:

- `RunScheduler.make_trigger` returns a `RunTrigger` with `universe` from settings and
  `as_of` defaulting to today.
- **Idle behavior test:** construct a `Dispatcher`; do NOT call `execute_run`; assert graph
  is empty — proves agents are idle until messaged.

**Update `orchestration/tests/test_p4_daily_loop.py` and `test_p4_celery_parity.py`**:

- Add assertion: `node_count(graph, "Message") >= 7` after a completed run (one per step
  attempted). This is the P4 exit assertion for supervisor message lineage.

**Coverage floor** — ratchet from 100.00; never lower. `agents/supervisor/` is new, so it
must be covered from the start.

## Steps

1. Branch `sprint-15-supervisor` off `main`.
2. Fix `steps.py` line 98 (one line) — run `make ci` to confirm nothing breaks.
3. Read `contracts/supervisor.py` + `orchestration/dispatcher.py` fully before writing the
   supervisor agent or dispatcher changes.
4. Update `contracts/supervisor.py` (add `DispatchRunRecord` + `record_dispatch_run`).
5. Implement `agents/supervisor/` (store, agent, settings, mission, `__init__`).
6. Add `step_record_dispatch_run` to `orchestration/steps.py`.
7. Update `orchestration/dispatcher.py` — add step tracking + `_record_run`; keep ≤ 150 lines.
8. Update `orchestration/bindings.py` to bind `SupervisorAgent`.
9. Write supervisor unit tests; update the two P4 pipeline tests; write scheduler tests.
10. Run the gate; confirm the updated P4 parity tests pass with `Message` node assertions.
    Push; hand back. Do not merge to `main`.

## Acceptance criteria

- `step_check_positions` no longer returns `None` on an empty `decisions` set (all-hold runs
  complete successfully).
- `SupervisorAgent.record_dispatch_run` writes one `Message` node per step; `report_fault`
  writes a `Fault` node; boundary meta-test green (`Message`/`Fault` single-writer verified).
- `Dispatcher.execute_run` calls `_record_run` before every return; step names tracked.
- `test_p4_daily_loop` and `test_p4_celery_parity` both assert `node_count(graph, "Message") >= 7`.
  **This is the P4 exit assertion.**
- `RunScheduler.make_trigger` returns a correctly populated `RunTrigger`; idle behavior test
  proves graph stays empty without a `execute_run` call.
- `dispatcher.py` ≤ 150 lines; all new modules headered, < 200 lines; tunables justified.
- `make ci` green at/above the coverage floor (4/4 import-linter contracts kept).

## Out of scope (do NOT build this sprint)

`dispatch_intent`, `system_status`, `flag_for_human` supervisor capabilities (P5); the
`Agent` and `Flag` graph labels (P5); a production cron/event loop that wakes the scheduler
(deployment infra); non-eager Celery worker with a real broker (integration-only); the
`Flag -[:RAISED]-> ...` edge (P5 human-review surface). Flag anything you think is needed
earlier.

## Handback report (paste into the PR / reply)

- Files added/changed and final line counts (confirm `dispatcher.py` ≤ 150,
  `supervisor/agent.py` ≤ 150).
- How step tracking is implemented in `execute_run` (local list vs. other approach).
- Whether the one-line `step_check_positions` fix required any test updates.
- Supervisor `owns_graph` boundary meta-test result (was `Message`/`Fault` previously
  unclaimed? did the meta-test need a change?).
- New coverage % and floor; the Message node count in the updated P4 parity tests.
- Anything that felt out of scope or needs a design decision.

The planning agent will review, confirm P4 exit criterion met, merge to `main`, and update
`docs/STATE.md` + `docs/build-plan.md`. After this sprint, P4 is complete and P5 begins.
