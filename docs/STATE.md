# Project State

**Last updated:** 2026-06-07 — Sprint 03 (Neo4j GraphStore) merged to `main`;
relational layer retired.

**How to read:** *Now* = being worked on. *Next* = queued, not started. *Parked* =
exists but inactive. *Shipped* = landed. Update at every transition.

---

## Now

**Between sprints.** [Sprint 04](sprints/sprint-04-provider-agent.md) shipped the **first
real agent** (fast-forward `fd1df0c`) — `provider`, the start of **P2**: sole holder of
market-data credentials, answering `get_market_data` + `get_regime` over the in-process
bus with a DI-1 integrity gate, deterministic regime classification, honest quality
accounting, and append-only provenance written to the `GraphStore`. It establishes the
agent-composition pattern every later agent copies (graph/source/settings injection,
`domain/`, `store.py` graph writes); secrets are `repr=False`; `agents` is now in the
coverage source. Gate is infra-free (fake data source + in-memory graph).

The kernel runtime spine (bus + `AgentBase` + Neo4j `GraphStore`) supports the slice; the
remaining P1 infra (distributed bus, observability, tool-binding, RAG vector) is
build-when-needed. Next P2 agents: **scanner**, then **analyst**.

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
