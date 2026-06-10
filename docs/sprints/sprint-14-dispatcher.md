# Sprint 14 — Dispatcher (P4 begins: event-driven daily loop)

**Status:** planned · **Branch:** `sprint-14-dispatcher` · **Build phase:** P4 (orchestration) · **Effort: M**

## Goal

Implement the `Dispatcher` in `orchestration/` — the component that replaces all manual
in-test sequencing with a single `execute_run(trigger)` call. It drives the complete 7-agent
paper loop (`provider → scanner → analyst → portfolio_manager → execution → monitor → reporter`)
by sending typed messages to the bus in the right order, handling faults at each step, and
returning a `RunResult`. **The P4 exit contribution is proven by a CeleryBus parity test: the
same run that passes on `InProcessBus` also passes on `CeleryBus` (eager mode) — proving the
distributed bus path end-to-end.**

## Why (context)

- P3 left a working 7-agent loop proven by test code that manually chains bus requests. P4
  replaces that manual sequencing with the dispatcher and puts it on the distributed bus.
- `orchestration/` sits **above** agents in the dependency direction: it may import `agents`,
  `contracts`, and `kernel`. Agents may NOT import `orchestration` (enforced by import-linter,
  KEPT). This is different from agents importing each other — orchestration is the wiring layer.
- Read first: `docs/sprints/README.md` (guardrails + gate); `docs/architecture.md` (layer
  diagram, the one rule, dependency direction); `.importlinter` (the four contracts —
  orchestration sits above agents, agents must not reach back); `docs/build-plan.md` P4;
  **all 7 agent `__init__.py` files** to know their public exports (`ProviderAgent`, etc.);
  `agents/reporter/tests/test_p3_reporter_slice.py` (the existing manual pipeline — the
  dispatcher replaces this sequencing); `kernel/bus.py` + `kernel/bus_celery.py` (both bus
  backends); `agents/execution/broker.py` (`PaperBroker`); `kernel/errors.py`
  (`fault_boundary`); `contracts/reporter.py` (`RunSnapshot`).
- Porting source: `agents/reporter/tests/p3_helpers.py` — the bind + sequence pattern becomes
  the dispatcher's runtime.

## Key design constraints (do not break)

- **Agents bind to the bus; the dispatcher sends messages.** The dispatcher calls
  `ProviderAgent(bus, ...).bind()` for each agent (same as the P3 test helper), then drives
  the loop by sending typed messages. It does NOT call agent methods directly.
- **Import direction.** `orchestration/` imports `agents.*`, `contracts.*`, and `kernel.*`.
  `agents.*` must never import from `orchestration` — the existing import-linter contract
  enforces this; it must stay green.
- **Fault at any step = graceful stop, not crash.** If `run_scan` returns no candidates, the
  dispatcher returns a `RunResult` with `completed=False` and a reason. If an agent raises,
  wrap in `fault_boundary` (reraise=False), record the fault, return early. A partially
  completed run is not an error — it's a valid outcome.
- **Paper stage only.** Inject `PaperBroker` for execution and `FakeDataSource` / a real
  `StooqDataSource` for the provider, based on `OrchestratorSettings`. The dispatcher does not
  know about live stages — that is P8.
- **No supervisor this sprint.** The supervisor agent (full capability gate, `dispatch_intent`,
  `report_fault`) is P5. For P4, the dispatcher uses the existing `FaultSink` / `fault_boundary`
  for fault recording. Do not stub out a supervisor or write to `Message` / `Agent` graph labels
  (those are owned by supervisor per `contracts/supervisor.py`).
- **Small files, headers, < 200 lines; no magic numbers.**

## Deliverables

1. **`orchestration/trigger.py`** — `RunTrigger(_Frozen)`: `run_id: str`, `universe: str`,
   `as_of: date`. `RunResult(_Frozen)`: `run_id: str`, `completed: bool`,
   `snapshot: RunSnapshot | None`, `steps_completed: int`, `reason: str | None`.
   Use `contracts.common._Frozen` for both.

2. **`orchestration/steps.py`** — one function per pipeline step, each returning its typed
   output or `None` on empty/fault:
   - `step_scan(bus, trigger) -> CandidateSet | None`
   - `step_analyze(bus, candidates) -> RecommendationSet | None`
   - `step_evaluate(bus, recommendations) -> OrderIntentSet | None`
   - `step_submit(bus, orders) -> ExecutionResult | None`
   - `step_check_positions(bus, pm_run_id) -> CloseDecisionSet | None`
   - `step_report(bus, pm_run_id) -> RunSnapshot | None`

   Each step wraps the bus request in `fault_boundary(sink, reraise=False)` and returns `None`
   on fault. The step functions are pure in the sense that they do not bind agents — binding
   is the dispatcher's job.

3. **`orchestration/dispatcher.py`** — `Dispatcher`:

   ```python
   class Dispatcher:
       def __init__(self, bus, graph, *, settings, source, broker, sink):
           # bind all 7 agents to the bus
       def execute_run(self, trigger: RunTrigger) -> RunResult:
           # sequence steps; return RunResult on first None or completion
   ```

   The constructor binds `ProviderAgent`, `ScannerAgent`, `AnalystAgent`,
   `PortfolioManagerAgent`, `ExecutionAgent`, `MonitorAgent`, `ReporterAgent` to the bus
   using appropriate settings. `execute_run` calls each `step_*` in order; stops and returns
   `RunResult(completed=False, steps_completed=N, reason=...)` if any step returns `None`.
   Keep `dispatcher.py` ≤ 150 lines — the step logic lives in `steps.py`.

4. **`orchestration/settings.py`** — `OrchestratorSettings(AgentSettings)`,
   `env_prefix="ORCHESTRATOR_"`. Justified tunables: `universe` (default `"sp500"`, why:
   paper-stage default scan universe), `provider_max_staleness_days` (default 7),
   `pm_starting_cash` (default `Decimal("100000.00")`). The `DataSource` and `Broker` ports
   are injected (not settings) so the dispatcher stays testable with `FakeDataSource` +
   `PaperBroker`.

5. **`orchestration/__init__.py`** — export `Dispatcher`, `RunTrigger`, `RunResult`.

6. **`orchestration/tests/test_dispatcher_unit.py`** — infra-free unit tests:
   - `execute_run` on an empty universe (scanner returns 0 candidates) → `RunResult(completed=False)`, no crash.
   - `execute_run` with a failing provider (FakeDataSource raises) → `RunResult(completed=False)` after step 1, fault recorded.
   - `step_analyze` with empty recommendations → `None` returned, no crash.

7. **`orchestration/tests/test_p4_daily_loop.py`** — end-to-end on `InProcessBus`:
   - Wire `Dispatcher` with `FakeDataSource` (entry bars) + `PaperBroker`; call
     `execute_run(trigger)`; assert `result.completed is True`, `result.snapshot` is not None,
     `result.snapshot.portfolio_metrics["positions_opened"] >= 1`; assert graph contains
     `Snapshot` and `TradeNarrative` nodes.

8. **`orchestration/tests/test_p4_celery_parity.py`** — **P4 exit test**:
   - Same scenario as `test_p4_daily_loop` but with `CeleryBus` (eager mode:
     `CELERY_TASK_ALWAYS_EAGER=True`). Assert the same `result.completed is True` and snapshot
     assertions pass. This proves the distributed bus path works end-to-end.
   - Mark with `@pytest.mark.integration` if a real broker is needed; eager mode should not
     require external infra.

9. **Coverage floor** — ratchet from 100.00; orchestration is now under coverage; never lower.

## Steps

1. Branch `sprint-14-dispatcher` off `main`.
2. Read all 7 agent `__init__.py` + `p3_helpers.py` before writing a line of dispatcher code.
3. `trigger.py`; `steps.py`; `dispatcher.py` (≤ 150 lines); `settings.py`; `__init__.py`.
4. Unit tests first (`test_dispatcher_unit.py`), then pipeline test, then CeleryBus parity.
5. Run the gate; confirm CeleryBus parity test passes. Push; hand back. Do not merge to `main`.

## Acceptance criteria

- `Dispatcher.execute_run()` drives all 7 agents from a single call; no agent imports
  `orchestration` (import-linter KEPT, all 4 contracts green).
- Empty universe → `RunResult(completed=False)`, no crash. Provider fault → graceful stop.
- `test_p4_daily_loop` passes on `InProcessBus`: `result.completed is True`, snapshot and
  narrative nodes in graph.
- **`test_p4_celery_parity` passes on `CeleryBus` (eager mode)** — P4 distributed-bus proof.
- All modules headered, < 200 lines; `dispatcher.py` ≤ 150; tunables justified.
- `make ci` green at/above the coverage floor.

## Out of scope (do NOT build this sprint)

The **supervisor agent** (full `dispatch_intent` / `system_status` / capability gate / hard-NO
surface — P5); `Message` / `Agent` graph label writes (supervisor-owned); a cron/wall-clock
scheduler (a follow-up P4 sprint once the dispatcher is green); non-eager Celery worker with a
real broker (integration-only, no infra in CI); the MCP tool binding for orchestration. Flag
anything you think is needed earlier.

## Handback report (paste into the PR / reply)

- Files added/changed and final line counts (confirm `dispatcher.py` ≤ 150).
- How agent binding is done in `Dispatcher.__init__` and how settings flow to each agent.
- Whether any step required a design change (e.g., `step_check_positions` needs the PM run_id
  from the execution result — confirm how that flows through).
- CeleryBus parity test: eager mode, any config needed, pass confirmed.
- New coverage % and floor; anything that felt out of scope.

The planning agent will review, merge to `main`, and update `docs/STATE.md` +
`docs/build-plan.md`. After this, P4 continues with the scheduler + supervisor message
lineage (Sprint 15).
