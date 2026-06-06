# Project State

**Last updated:** 2026-06-07 — graph-tech decided: Neo4j as the single store
(ADR-0001); Sprint 02 relational adapter superseded.

**How to read:** *Now* = being worked on. *Next* = queued, not started. *Parked* =
exists but inactive. *Shipped* = landed. Update at every transition.

---

## Now

**Decision recorded — Neo4j as the single primary store**
([ADR-0001](decisions/0001-neo4j-primary-store.md)): one schema-flexible graph store
for transactional records, provenance, and RAG — no relational DB and no migrations.
This **supersedes [Sprint 02](sprints/sprint-02-persistence.md)'s relational
persistence adapter**: the next storage sprint retires `kernel/persistence.py` +
`alembic/`, drops SQLAlchemy/Alembic, and builds the kernel `GraphStore` (Neo4j)
adapter (nodes/edges + a vector index for RAG) behind a protocol.

P1 (kernel runtime) continues — see Next. The PRD, architecture, and build-plan are
updated to the single-store model; the long-tail propagation (observability,
error-handling, README) and all code changes are tracked in the ADR.

Quality gate (last green on `main`, pre-pivot): ruff, format, mypy, import-linter
(4/4), size + header guards, 64 tests at 99.17% — the relational-adapter tests retire
with the pivot.

## Next

- **Storage pivot (next sprint):** retire the relational adapter + Alembic; build the
  Neo4j `GraphStore` adapter (nodes/edges + vector index for RAG) behind a protocol;
  add a Neo4j test service; rename the single-writer invariant to per-label.
- Then the rest of P1: distributed (Celery) bus, observability/metrics adapter,
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
