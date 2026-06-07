# Project State

**Last updated:** 2026-06-07 — Sprint 03 (Neo4j GraphStore) merged to `main`;
relational layer retired.

**How to read:** *Now* = being worked on. *Next* = queued, not started. *Parked* =
exists but inactive. *Shipped* = landed. Update at every transition.

---

## Now

**Between sprints.** [Sprint 03](sprints/sprint-03-neo4j-store.md) shipped the storage
pivot (fast-forward `ba2f42c`): a kernel `GraphStore` protocol with an `InMemoryGraphStore`
(deterministic, infra-free unit gate) and a `Neo4jGraphStore` (Cypher-injection-guarded,
unit-tested via a fake driver), append-only by construction, with the relational adapter +
Alembic fully retired and the boundary map reconciled to single-writer-per-label
([ADR-0001](decisions/0001-neo4j-primary-store.md)).

P1 continues — the next sprint is being scoped (see Next).

Quality gate (green on `main`): ruff, format, mypy (40 files), import-linter (4/4 —
"Kernel is pure plumbing" KEPT), size + header guards, **67 tests (+1 skipped live-Neo4j)
at 99.52% coverage** (floor raised to 99.5). No external infra needed.

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
