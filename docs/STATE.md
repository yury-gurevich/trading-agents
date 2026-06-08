# Project State

**Last updated:** 2026-06-08 — Sprint 06 (analyst) merged; **P2 first vertical slice complete.**

**How to read:** *Now* = being worked on. *Next* = queued, not started. *Parked* =
exists but inactive. *Shipped* = landed. Update at every transition.

---

## Now

**P2 — first vertical slice — COMPLETE.** [Sprint 06](sprints/sprint-06-analyst-agent.md)
shipped the **analyst** (fast-forward `d44f8f2`), closing `provider → scanner → analyst`.
The analyst scores a scanner `CandidateSet` into `Recommendation`s by calling `provider`
(market data + regime) over the bus, gates confidence by `base_min_confidence`, gives
explainable rejections, and writes `Recommendation -DERIVED_FROM-> Candidate`. The **P2 exit
is met**: a full-slice integration test (all three agents on one bus) proves the provenance
chain `Recommendation → Candidate → ScanRun → MarketSnapshot`, with no agent importing another.

Three real agents (`provider`, `scanner`, `analyst`) now run end-to-end on the in-process
bus, gate infra-free. **P3 (the decision loop)** is the next phase — see Next.

Quality gate (green on `main`): ruff, format, mypy (74 files), import-linter (4/4 — agent
isolation KEPT), size + header guards, **101 tests (+2 skipped live) at 99.73%** (floor 99.72).

## Next

- **P3 — the decision loop** (`portfolio_manager → execution → monitor → reporter`): size +
  risk-check recommendations, submit idempotently to a paper broker, open/close positions,
  stitch the run narrative. *(Or finish the deferred P1 infra first — operator's call.)*
- Deferred P1 infra (build-when-needed): the distributed (Celery) bus, the
  observability/metrics adapter, the contract→tool-interface binding, the RAG vector index.

## Workflow

The planning agent (expensive) writes sprint handovers and maintains documentation
and progress; a coding agent (cheap) implements one active sprint at a time on its
own branch and hands back. See `docs/sprints/README.md`.

## Parked

- (none)

## Shipped

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
