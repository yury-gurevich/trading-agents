# Project State

**Last updated:** 2026-06-08 — Sprint 05 (scanner) opened; Sprint 04 (provider) shipped.

**How to read:** *Now* = being worked on. *Next* = queued, not started. *Parked* =
exists but inactive. *Shipped* = landed. Update at every transition.

---

## Now

**Sprint 05 active:** [Scanner agent](sprints/sprint-05-scanner-agent.md) — the second P2
agent and the **first agent-to-agent call**: scanner reduces a named universe to a ranked,
explained `CandidateSet` by requesting `get_market_data` from `provider` over the bus (never
importing it), and writes cross-agent provenance (`Candidate → ScanRun → MarketSnapshot`).
Establishes the inter-agent request pattern every later agent copies. Handover written;
awaiting the coding agent on branch `sprint-05-scanner-agent`. Gate stays infra-free
(in-process bus + a real provider on a fake data source + in-memory graph).

Shipped: `provider` (Sprint 04) — sole data-API holder, `get_market_data` + `get_regime`,
DI-1 integrity gate + regime classifier, append-only provenance; established the
agent-composition pattern and added `agents` to the coverage source.

Quality gate (green on `main`): ruff, format, mypy (50 files), import-linter (4/4 —
agent isolation KEPT), size + header guards, **79 tests (+2 skipped live) at 99.62%
coverage** (floor raised to 99.6).

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
