# Project State

**Last updated:** 2026-06-09 — Sprint 07 (distributed bus) merged; both bus backends done.

**How to read:** *Now* = being worked on. *Next* = queued, not started. *Parked* =
exists but inactive. *Shipped* = landed. Update at every transition.

---

## Now

**Between sprints.** [Sprint 07](sprints/sprint-07-distributed-bus.md) shipped the
**distributed (Celery) bus** (fast-forward `4f4f0f2`) — a `CeleryBus` implementing the same
`MessageBus` protocol as `InProcessBus`, with identical semantics, tested in Celery **eager
mode** (no broker). The **P1 bus exit is met**: the same `EchoAgent` answers identically over
both backends (parity test); a real-broker round-trip is integration-marked.

State of the system: kernel runtime (both bus backends + `AgentBase` + Neo4j `GraphStore`)
and the P2 slice (`provider → scanner → analyst`, full provenance) are done. P1's remaining
infra — the observability/metrics adapter, the MCP tool-binding, the RAG vector index — is
build-when-needed. P3 (the decision loop) is the other open front.

Quality gate (green on `main`): ruff, format, mypy (75 files), import-linter (4/4 — kernel
pure + agent isolation KEPT), size + header guards, **108 tests (+3 skipped live/broker) at
99.74%** (floor 99.74).

## Next

- Remaining P1 infra after the bus (build-when-needed): the observability/metrics adapter,
  the contract→tool-interface (MCP) binding, the RAG vector index.
- **P3 — the decision loop** (`portfolio_manager → execution → monitor → reporter`): sizing +
  risk-checks, a paper broker, position lifecycle, and the stitched run narrative.

## Workflow

The planning agent (expensive) writes sprint handovers and maintains documentation
and progress; a coding agent (cheap) implements one active sprint at a time on its
own branch and hands back. See `docs/sprints/README.md`.

## Parked

- (none)

## Shipped

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
