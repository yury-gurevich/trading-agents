# Project State

**Last updated:** 2026-06-06 — Sprint 01 merged; Sprint 02 (persistence) opened.

**How to read:** *Now* = being worked on. *Next* = queued, not started. *Parked* =
exists but inactive. *Shipped* = landed. Update at every transition.

---

## Now

**Sprint 02 active:** [Persistence](sprints/sprint-02-persistence.md) — the kernel's
domain-pure relational adapter (SQLAlchemy 2.0 `Base` + fault-wrapped session) and
an Alembic migration harness, proven on local SQLite with no external infra. No
agent tables yet; it's the substrate each agent's future `store.py` will stand on.
Handover written; awaiting the coding agent on branch `sprint-02-persistence`.

Already on `main`: [Sprint 01](sprints/sprint-01-kernel-runtime.md) shipped the
runtime spine (fast-forward `97c9db7`) — the in-process bus (`kernel/bus.py`), the
contract-bound `AgentBase` (`kernel/agent.py`), and a `FaultCapture` so a
non-reraising `fault_boundary` can report what it caught. `kernel/` stays domain-pure.

Quality gate (green on `main`): ruff, format, mypy (36 files), import-linter
(4/4 — "Kernel is pure plumbing" KEPT), size + header guards,
**58 tests at 99.12% coverage** (floor raised 95 → 99.1).

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
