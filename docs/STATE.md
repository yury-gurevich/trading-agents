# Project State

**Last updated:** 2026-06-06 — Sprint 02 (relational persistence) merged to `main`.

**How to read:** *Now* = being worked on. *Next* = queued, not started. *Parked* =
exists but inactive. *Shipped* = landed. Update at every transition.

---

## Now

**Between sprints.** [Sprint 02](sprints/sprint-02-persistence.md) shipped the kernel's
domain-pure relational persistence adapter (SQLAlchemy 2.0 `Base`, `PersistenceSettings`,
and a fault-wrapped `Database.session()`) plus an Alembic migration harness, proven on
local SQLite with no external infra (fast-forward `ad53a5d`). No agent tables yet — it's
the substrate each agent's future `store.py` will stand on. Also fixed `.env.example`
tracking (`.gitignore` `.env.*` had silently excluded the template).

P1 (kernel runtime) continues — the next sprint is being scoped (see Next).

Quality gate (green on `main`): ruff, format, mypy (37 files), import-linter
(4/4 — "Kernel is pure plumbing" KEPT), size + header guards,
**64 tests at 99.17% coverage** (floor raised 99.1 → 99.17).

## Next

- Finish P1 after persistence: the Neo4j graph adapter, the distributed (Celery)
  bus, the observability/metrics adapter, and the contract→tool-interface binding.
- Then **P2 — first vertical slice** (`provider → scanner → analyst`).

## Workflow

The planning agent (expensive) writes sprint handovers and maintains documentation
and progress; a coding agent (cheap) implements one active sprint at a time on its
own branch and hands back. See `docs/sprints/README.md`.

## Parked

- (none)

## Shipped

- **Sprint 02 — Relational persistence adapter** (P1, partial). Domain-pure
  SQLAlchemy 2.0 `Base` + `PersistenceSettings` + a fault-wrapped
  `Database.session()`, plus an Alembic harness with an empty baseline, proven on
  SQLite (round-trip, commit, rollback+fault, migration smoke). 64 tests, floor
  raised to 99.17; `.env.example` now tracked.
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
