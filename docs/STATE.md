# Project State

**Last updated:** 2026-06-07 — graph-tech decided: Neo4j as the single store
(ADR-0001); Sprint 02 relational adapter superseded.

**How to read:** *Now* = being worked on. *Next* = queued, not started. *Parked* =
exists but inactive. *Shipped* = landed. Update at every transition.

---

## Now

**Sprint 03 active:** [Neo4j GraphStore](sprints/sprint-03-neo4j-store.md) — implements
[ADR-0001](decisions/0001-neo4j-primary-store.md): retire the relational adapter +
Alembic, stand up a `GraphStore` protocol with an in-memory backend (deterministic,
infra-free unit gate) and a `Neo4jGraphStore` (real, under an `integration` marker), and
reconcile the boundary map to single-writer-per-label. Handover written; awaiting the
coding agent on branch `sprint-03-neo4j-store`. The RAG vector index is a fast-follow.

Already settled (ADR-0001): one schema-flexible Neo4j store for transactional records,
provenance, and RAG — no relational DB, no migrations. The PRD, architecture, build-plan,
observability, and README are updated to the single-store model.

Quality gate (last green on `main`, pre-pivot): ruff, format, mypy, import-linter (4/4),
size + header guards, 64 tests at 99.17% — the relational-adapter tests retire with the pivot.

## Next

- The RAG vector index + `vector_search` on the `GraphStore` (fast-follow after Sprint 03).
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
