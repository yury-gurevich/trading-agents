# Sprint 07 — Distributed (Celery) bus backend (finishes the P1 bus)

**Status:** active · **Branch:** `sprint-07-distributed-bus` · **Build phase:** P1 (kernel runtime — bus completion)

## Goal

Add the **distributed bus backend** — a `CeleryBus` that implements the same kernel
`MessageBus` protocol as `InProcessBus`, so the *same* agent contract binds to either
transport without change. Prove the **P1 exit criterion**: a trivial echo agent answers a
typed request **over both bus backends** with identical observable behaviour. The gate runs
Celery in **eager mode** (no broker); a real-broker round-trip is integration-marked and
skips without Redis.

## Why (context)

- P1's exit names exactly this: *"an echo agent answers a typed request over both bus
  backends."* The in-process backend shipped in Sprint 01; this completes the pair.
- It mirrors a pattern already used twice: a `Protocol` with swappable backends
  (`MessageBus`: `InProcessBus` → `CeleryBus`; `GraphStore`: `InMemoryGraphStore` →
  `Neo4jGraphStore`). The kernel `__init__` docstring already reserves "distributed bus …
  adapters join later"; `celery>=5.4` + `redis>=5.0` are in the `runtime` extra.
- This backend changes **deployment, not logic** (build-plan principle): agents and flows
  are unchanged; the distributed backend lets an agent be a worker that idles until messaged.
  The orchestration dispatcher/workers/queue-routing that *use* it are **P4**, not this sprint.
- Read first: `docs/sprints/README.md` (guardrails + gate); **`kernel/bus.py`** (the
  `MessageBus` Protocol + `InProcessBus` — the exact semantics to mirror) and
  `tests/test_bus.py` (the four behaviours + the `EchoAgent` pattern); `kernel/agent.py`
  (`AgentBase.bind` calls `bus.register`); `kernel/envelope.py`, `kernel/errors.py`
  (`fault_boundary`), `kernel/config.py` (`AgentSettings`/`tunable`); `kernel/graph_neo4j.py`
  (a kernel backend that reads infra settings + is unit-tested via a fake — the shape to
  copy); `docs/architecture.md` §"Communication" (the two-backend design); `.env.example`
  (`CELERY_BROKER_URL`).

## Key design constraints (do not break)

- **Identical observable semantics to `InProcessBus`.** `CeleryBus` must produce the same
  results for the four behaviours: round-trip → `response` (`correlation_id == request.id`,
  payload = handler output); inbound-validation failure → `error` message + a recorded fault;
  handler raise → `error` message + a recorded fault (`source_module`); unknown
  `(recipient, capability)` → `error` message, never an exception. Re-use `fault_boundary`
  (module `"kernel.bus_celery"`), exactly like `InProcessBus`.
- **Same `MessageBus` Protocol.** `register(recipient, capability, handler)` and
  `request(message) -> AgentMessage`. `AgentBase` already targets this Protocol — it must
  bind to `CeleryBus` with **zero agent changes**.
- **Kernel stays pure.** `kernel/bus_celery.py` imports `celery` (external infra, already in
  the mypy overrides) but nothing from `contracts`/`agents`. `import-linter` "Kernel is pure
  plumbing" KEPT. The orchestration app/workers that wire queues are out of scope (P4).
- **Gate is infra-free.** Tests configure Celery `task_always_eager=True` (+
  `task_eager_propagates`) so dispatch runs synchronously in-process — no Redis. A real-broker
  test is `@pytest.mark.integration` and skips without `CELERY_BROKER_URL`/`REDIS`.
- **No magic numbers / headers / < 200 lines.** Any timeout/knob is a justified `tunable`.

## Suggested shape (latitude on the internals)

Mirror `InProcessBus`: keep a handler registry keyed by `(recipient, capability)`, and a
**single generic Celery task** that looks the handler up and runs it inside `fault_boundary`,
returning a typed result (e.g. `{"ok": payload}` or `{"error": {"error_type", "message"}}`).
`request` dispatches that task (`.apply_async(...).get(timeout=...)`; synchronous in eager
mode) and builds the `response`/`error` `AgentMessage` from the result — unknown capability
short-circuits to an `error` message before dispatch, as in `InProcessBus`. `CeleryBusSettings`
reads `CELERY_BROKER_URL` (default an eager/in-memory configuration suitable for tests).

> **Distributed fault-sink note (record, don't solve here):** in eager mode the worker and
> requester share one process, so the fault sink behaves exactly like `InProcessBus`. In a
> real broker deployment the handler runs in a *worker* process, so its sink is the worker's
> — which (per the architecture) publishes faults to the supervisor's central channel. Wiring
> that worker-side publication is **P4**; flag it, don't build it now.

## Deliverables

1. **`kernel/bus_celery.py`** — `CeleryBus` (implements `MessageBus`) + `CeleryBusSettings`
   (`AgentSettings`, `CELERY_BROKER_URL`, any timeout as a `tunable`). Constructor takes an
   optional `FaultSink` (default `CollectingFaultSink`), like `InProcessBus`. Headered, < 200
   lines.
2. **`kernel/__init__.py`** — export `CeleryBus` (and `CeleryBusSettings`).
3. **Dependencies** — add `celery>=5.4` to the `dev` group so `uv sync` installs it for the
   gate (it stays in the `runtime` extra). `redis` stays runtime-only (the eager gate needs
   no broker). Confirm `celery` is in the mypy ignore-missing overrides (it is).
4. **`tests/test_bus_celery.py`** — the **four behaviours** from `tests/test_bus.py`, against
   `CeleryBus` in eager mode (reuse or mirror the test-only `EchoAgent`/contract). Plus a
   **both-backends parity test**: the same `EchoAgent` answers identically over `InProcessBus`
   and `CeleryBus` (parametrize) — this is the P1-exit demonstration. Plus a real-broker
   round-trip `@pytest.mark.integration` that **skips** without `CELERY_BROKER_URL`.
5. Re-tune the coverage floor in `pyproject.toml` (both `--cov-fail-under` and
   `[tool.coverage.report] fail_under`) to the new measured value; never lower it. (`celery`
   internals are skipped from coverage via the existing overrides; keep `CeleryBus` thin and
   `# pragma: no cover` only genuinely broker-only lines.)

## Steps

1. Branch `sprint-07-distributed-bus` off `main`.
2. Write `kernel/bus_celery.py`; export from `__init__`; add `celery` to `dev`; `uv sync`.
3. Write `tests/test_bus_celery.py` (four behaviours + parity + integration-skip).
4. Run the gate; re-tune the floor. Push; hand back. Do not merge to `main`.

## Acceptance criteria

- `CeleryBus` implements `MessageBus`; an `EchoAgent` binds to it **unchanged** and answers a
  typed request; the four behaviours match `InProcessBus` exactly.
- The both-backends parity test passes in eager mode — **P1 exit met**.
- `import-linter` "Kernel is pure plumbing" KEPT; boundary meta-test green.
- Gate is **infra-free** (eager mode, no Redis); the real-broker test skips cleanly without
  `CELERY_BROKER_URL`.
- All modules headered, < 200 lines; tunables justified; `make ci` green at/above the
  re-tuned floor.

## Out of scope (do NOT build this sprint)

The orchestration layer (dispatcher, worker entrypoints, queue/routing, the scheduler that
issues run triggers) — that is **P4**; real-broker deployment/ops; worker-side fault
publication to the supervisor (flagged above); observability/metrics; MCP; the RAG vector
index. Flag anything you think is needed earlier.

## Handback report (paste into the PR / reply)

- Files added/changed and final line counts; the `CeleryBus` dispatch/result shape and how
  eager mode is configured for the gate.
- New coverage % and the re-tuned floor; confirmation the both-backends parity test passes.
- Any design decision worth recording (e.g. the worker-side fault-sink note) or anything that
  felt out of scope.

The planning agent will review, merge to `main`, and update `docs/STATE.md` +
`docs/build-plan.md`.
