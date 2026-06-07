# Project State

**Last updated:** 2026-06-07 — Sprint 03 (Neo4j GraphStore) merged to `main`;
relational layer retired.

**How to read:** *Now* = being worked on. *Next* = queued, not started. *Parked* =
exists but inactive. *Shipped* = landed. Update at every transition.

---

## Now

**Sprint 04 active:** [Provider agent](sprints/sprint-04-provider-agent.md) — the first
real agent and the start of **P2**. Sole holder of market-data credentials; answers
`get_market_data` + `get_regime` over the in-process bus with validated data, honest
quality accounting, and provenance written to the Neo4j `GraphStore`. Establishes the
agent patterns every later agent copies (graph/source/settings injection, `domain/`,
data-integrity gates, provenance writes). Gate stays infra-free via a fake data source +
the in-memory graph. Handover written; awaiting the coding agent on branch
`sprint-04-provider-agent`.

The kernel runtime spine is in place (bus + `AgentBase` + Neo4j `GraphStore`); the
remaining P1 infra (distributed bus, observability, tool-binding, RAG vector) is
build-when-needed and does not block this in-process slice.

Quality gate (green on `main`): ruff, format, mypy (40 files), import-linter (4/4),
size + header guards, **67 tests at 99.52%** (floor 99.5).

## Next

- The RAG vector index + `vector_search` on the `GraphStore` (fast-follow).
- The rest of P1: distributed (Celery) bus, observability/metrics adapter,
  contract→tool-interface binding.
- Then **P2 — first vertical slice** (`provider → scanner → analyst`).

## Workflow

The planning agent (expensive) writes sprint handovers and maintains documentation
and progress; a coding agent (cheap) implements one active sprint at a time on its
own branch and hands back. See `docs/sprints/README.md`.

## Parked

- (none)

## Shipped

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
