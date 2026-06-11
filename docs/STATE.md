# Project State

**Last updated:** 2026-06-11 — Sprint 18 (surfaces foundation + CLI) shipped. **P6 active.**

**How to read:** *Now* = being worked on. *Next* = queued, not started. *Parked* =
exists but inactive. *Shipped* = landed. Update at every transition.

---

## Now

**P6 active. Sprint 18 shipped.** Surfaces foundation + CLI landed: `resolve_flag` append-only
fix (FlagResolution node), graph query projections (`runs`, `positions`, `health`), and a working
CLI (`status`, `runs`, `run <id>`, `positions`, `command`). 251 tests at 100% (floor 100.00).

State: full agent roster implemented; surfaces layer wired (`surfaces/queries/`, `surfaces/cli.py`,
`surfaces/context.py`); `FlagResolution` append-node pattern; `test_context` / `paper_context`
factories. CLI tests are infra-free (InMemoryGraphStore + FakeLLMClient).

Known gap: `surfaces/queries/_graph.py::nodes_by_label` uses `getattr(graph, "_nodes", None)` —
returns empty tuples silently against the Neo4j backend. The `GraphStore` protocol has no
`list_nodes(label)` method. Surface queries work perfectly in CI (InMemoryGraphStore) but show no
data in production with Neo4j. **Must fix in Sprint 19 (Part A) before P6 closes.**

## Next

- **Sprint 19 — GraphStore `list_nodes` + position lifecycle** (P6 continues):
  Part A: add `list_nodes(label: str) → tuple[Node, ...]` to `GraphStore` protocol + both backends;
  remove `._nodes` access from `surfaces/queries/_graph.py` and `health.py`. Part B: extract
  `cli_commands.py` from `cli.py` (at hard cap 150L); `surfaces/queries/lifecycle.py`
  (`PositionLifecycle`, `position_lifecycle`, `all_position_lifecycles`); `surfaces/queries/flags.py`
  (`FlagView`, `pending_flags`); `cli position <pos_id>` + `cli flags` commands.
  Plan: `docs/sprints/sprint-19-list-nodes-lifecycle.md`.
- Build-when-needed: MCP tool-binding (`interpret` + `dispatch_intent`), RAG vector index.

## Workflow

The planning agent (expensive) writes sprint handovers and maintains documentation
and progress; a coding agent (cheap) implements one active sprint at a time on its
own branch and hands back. See `docs/sprints/README.md`.

## Parked

- (none)

## Shipped

- **Sprint 18 — Surfaces foundation + CLI** (P6 begins). `resolve_flag` append-only fix:
  `_replace_node` deleted; `FlagResolution` node appended with `RESOLVES` edge; `health.py` counts
  open flags by `FlagResolution` absence. `surfaces/queries/` projections (`runs.py` 111L,
  `positions.py` 79L, `health.py` 72L); `surfaces/cli.py` 125L; `surfaces/context.py` 110L;
  `surfaces/render.py` 100L. CLI tests infra-free (InMemoryGraphStore + FakeLLMClient). 251 tests,
  floor 100.00. Known gap: `nodes_by_label` uses `._nodes` — silently empty for Neo4j; fix in S19.
- **Sprint 17 — Supervisor capability gate** (P5 — **exit criterion met**). `dispatch_intent`
  enforces hard-NO → confirmation gate → capability matrix in order; confirmation writes/resolves
  `Flag` nodes; `system_status` queries live graph health; `flag_for_human` writes `Flag` nodes
  idempotently. `gate.py` (58L) holds the routing logic cleanly separate from agent.py (173L).
  P5 exit test: `operator.interpret → supervisor.dispatch_intent` with `CommandAudit` + `Message`
  nodes confirmed; policy-parity test (dashboard == MCP) green.
- **Sprint 16 — Operator agent** (P5 begun). `LLMClient` protocol + `FakeLLMClient` in kernel;
  `AnthropicLLMClient` in `agents/operator/`; `OperatorAgent` with `interpret` (all 10 families,
  confirmation policy hardcoded in grammar) and `explain` (graph evidence + LLM narration);
  `CommandAudit -[:PRODUCED_BY]-> LLMCall` + `CommandAudit -[:RESULTED_IN]-> Intent` provenance;
  `domain/result.py` extracted to hold parsing helpers. `agent.py` 148L. 237 tests, floor 100.
- **Sprint 15 — Scheduler + supervisor message lineage** (P4 — **exit criterion met**).
  `step_check_positions` all-hold fix; `SupervisorAgent` (`record_dispatch_run` writes one
  `Message` node per step, `report_fault` writes `Fault` nodes); `RunScheduler` factory;
  dispatcher tracks steps locally and calls `_finish()` before every return; idle proof test.
  Dispatcher refactored: `run_outcome.py` (stop-reason constants), `lineage.py` (position
  traversal), `narratives.py` (fan-out) extracted to stay ≤ 150 lines. 208 tests, floor 100.
  **P4 exit: daily loop on distributed bus, event-driven, supervisor recording message lineage.**
- **Sprint 14 — Dispatcher** (P4 begun). `Dispatcher` in `orchestration/` binds all 7 agents
  and drives `execute_run(trigger)` through scan→analyze→evaluate→submit→check_positions→report
  in order; graceful stop on fault/empty at each step. `orchestration/bindings.py` separates
  agent binding from routing; `orchestration/steps.py` (160 lines) houses typed step functions.
  CeleryBus fix: `disable_sync_subtasks=not eager` unblocks nested calls in eager mode.
  P4 CeleryBus parity test green. 195 tests, floor 100. Near-limit: `steps.py` (160),
  `tests/helpers.py` (161), `test_dispatcher_unit.py` (167) — warn-band only, split on next touch.
- **Sprint 13 — Reporter agent** (P3 — **exit criterion met**). Read-only graph traversal
  produces `RunSnapshot` (portfolio/signal metrics, headline) and `TradeNarrative` (scan-to-exit
  story per position). `Snapshot -[:SUMMARISES]-> PMRun` and `TradeNarrative -[:NARRATES]->
  Position` written. `agent.py` 88 lines. 185 tests, floor 100.
- **Sprint 12 — Monitor agent** (P3). Opens positions from fills (`PMRun → OrderIntent → Fill`
  traversal), evaluates stop/target/time exit rules (integer PCT_SCALE arithmetic), drives
  `execution.execute_close` on the bus, writes `CloseDecision -[:CLOSES]-> Position` and
  `Fill -[:OPENS]-> Position` lineage. 6-agent pipeline test proves the complete P3 provenance
  chain. `MonitorRun` added to `contracts/monitor.py` `owns_graph`. 171 tests, floor 100.
- **Sprint 11 — Execution agent** (P3). Idempotent `PaperBroker` (dedupes by
  `f"{run_id}:{ticker}:{side}"`), four capabilities, `Fill -[:EXECUTES]-> OrderIntent` lineage.
  No `ExecRun` parent — fills keyed directly by idempotency key. 100% coverage.
- **Sprint 10 — Audit-truth & rigor hardening** (P3). Durable PM rejection evidence (`Rejection`
  nodes + lineage); contract value validators; deep-frozen graph props; matched InMemory/Neo4j
  edge identity (parity test); lazily-installed Neo4j uniqueness constraints; split the tight
  kernel modules; Stooq/MA/tie-break fixes. 144 tests; floor de-pinned 100 → 99.5.
- **Sprint 09 — Portfolio manager** (P3 begun). Sizes + risk-checks recommendations into
  `OrderIntent`s (two provider bus calls, deterministic sizing, explainable rejections, money as
  integer cents); `OrderIntent -[:APPROVES]-> Recommendation` lineage; 4-agent pipeline test green.
  130 tests, floor 100. *Audit-truth follow-ups (persist rejections, contract validators) go to
  the hardening sprint.*
- **Sprint 08 — Observability metrics adapter** (P1). Vendor-neutral `Metrics` protocol
  (`NullMetrics` default + `PrometheusMetrics` private-registry backend, no server); both buses
  instrumented for throughput/latency/outcome; `MeteredFaultSink` for fault-rate by source.
  112 tests, floor 99.75.
- **Sprint 07 — Distributed (Celery) bus** (P1). `CeleryBus` implementing `MessageBus` with
  `InProcessBus`-identical semantics (the four behaviours), tested in eager mode; a
  both-backends parity test proves the P1 bus exit; real-broker round-trip integration-marked.
  108 tests, floor 99.74.
- **Sprint 06 — Analyst agent** (P2 — **slice complete**). `analyze` +
  `explain_recommendation`; two provider bus calls (market data + regime), technical scoring,
  confidence gating by `base_min_confidence`, explainable rejections, and `Recommendation
  -DERIVED_FROM-> Candidate` lineage. The full-slice integration test proves the P2-exit
  chain `Recommendation → Candidate → ScanRun → MarketSnapshot`. 101 tests, floor 99.72.
- **Sprint 05 — Scanner agent** (P2). First agent-to-agent call: `run_scan` +
  `explain_filter` request `get_market_data` from `provider` over the bus (no import),
  deterministic filters/ranking with justified tunables, honest degraded handling, and
  cross-agent provenance (`Candidate → ScanRun → MarketSnapshot`). 87 tests, floor 99.67.
- **Sprint 04 — Provider agent** (P2, first agent). `provider` over the in-process bus:
  `get_market_data` + `get_regime`, `DataSource` port (`FakeDataSource` for the gate,
  keyless `StooqDataSource` network-gated), DI-1 integrity gate + VIX regime classifier
  (justified tunables), append-only provenance to the `GraphStore`, secrets `repr=False`.
  Established the agent-composition pattern; `agents` added to coverage. 79 tests, floor 99.6.
- **Sprint 03 — Neo4j GraphStore** (P1, partial). Kernel `GraphStore` protocol +
  `InMemoryGraphStore` + `Neo4jGraphStore` (fake-driver unit tests; live test skips without
  `NEO4J_TEST_URI`); append-only enforced (no prop overwrite), Cypher-injection guarded.
  Retired the relational adapter + Alembic; boundary map → single-writer-per-label. 67
  tests, floor raised to 99.5.
- **Sprint 02 — Relational persistence adapter** (P1, partial; **superseded by
  [ADR-0001](decisions/0001-neo4j-primary-store.md)** — relational store dropped for
  Neo4j). Domain-pure SQLAlchemy 2.0 `Base` + `PersistenceSettings` + a fault-wrapped
  `Database.session()`, plus an Alembic harness; 64 tests; `.env.example` now tracked.
- **Sprint 01 — Kernel runtime spine** (P1, partial). In-process bus + contract-
  bound `AgentBase` with inbound/outbound payload validation and the fault
  channel wired end-to-end; four behaviours covered (round-trip, inbound
  validation, handler raise, unknown capability). 58 tests, floor 99.1.
- **P0 — Boundary map + foundations.** 12 agent contracts + missions, kernel
  descriptors, config governance, central fault channel, the curator agent,
  self-enforcing guards, CI parity. First private push to GitHub.

---

## Pointers

- Product intent: `docs/PRD.md`
- Structure & rules: `docs/architecture.md`
- Sequenced plan: `docs/build-plan.md`
- Configuration governance: `docs/configuration.md`
- Error handling: `docs/error-handling.md`
- Observability & historical data: `docs/observability.md`
- Per-agent charters: `agents/<name>/mission.md`
- Machine boundaries: `contracts/<name>.py`
