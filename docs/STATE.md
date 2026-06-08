# Project State

**Last updated:** 2026-06-08 — Sprint 05 (scanner) merged to `main`.

**How to read:** *Now* = being worked on. *Next* = queued, not started. *Parked* =
exists but inactive. *Shipped* = landed. Update at every transition.

---

## Now

**Between sprints.** [Sprint 05](sprints/sprint-05-scanner-agent.md) shipped the **scanner**
(fast-forward `0898be1`) — the second P2 agent and the **first agent-to-agent call**: it
reduces a configured universe to a ranked, explained `CandidateSet` by requesting
`get_market_data` from `provider` over the bus (no import), with deterministic filters +
ranking and honest degraded handling, and writes cross-agent provenance
(`Candidate -SURVIVED-> ScanRun -DERIVED_FROM-> MarketSnapshot`). Two real agents now run
end-to-end on one bus.

P2 slice: `provider` → `scanner` shipped; **`analyst`** is the last agent (turn candidates
into scored, evidence-backed recommendations).

Quality gate (green on `main`): ruff, format, mypy (60 files), import-linter (4/4 — agent
isolation KEPT), size + header guards, **87 tests (+2 skipped live) at 99.68%** (floor 99.67).

## Next

- **`analyst`** — the last P2 agent: turn candidates into scored, evidence-backed
  recommendations, closing the `provider → scanner → analyst` slice.
- Deferred P1 infra (build-when-needed): the distributed (Celery) bus, the
  observability/metrics adapter, the contract→tool-interface binding, the RAG vector index.

## Workflow

The planning agent (expensive) writes sprint handovers and maintains documentation
and progress; a coding agent (cheap) implements one active sprint at a time on its
own branch and hands back. See `docs/sprints/README.md`.

## Parked

- (none)

## Shipped

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
