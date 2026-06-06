# Project State

**Last updated:** 2026-06-06 — repository bootstrapped; boundary map + foundations
complete; first private push.

**How to read:** *Now* = being worked on. *Next* = queued, not started. *Parked* =
exists but inactive. *Shipped* = landed. Update at every transition.

---

## Now

Foundational. The boundary map and the cross-cutting foundations are in place and
self-enforcing:

- `kernel/` — contract descriptors, A2A message envelope, the justified-tunable
  config primitive (`config.py`), and the central fault channel (`errors.py`).
- `contracts/` — shared vocabulary + **12** typed agent contracts.
- `agents/<name>/` — mission charter + package stub for all 12 agents.
- Guards: boundary meta-test (single-writer, exclusive I/O, typed boundaries),
  module size (warn 150 / hard 200), coding-agent header (`Agent:`/`Role:`).
- CI/test toolchain mirrors the reference conventions (ruff, mypy --strict,
  import-linter, pytest + coverage ratchet, detect-secrets, pip-audit) — green.

Quality gate locally: ruff, format, mypy (34 files), import-linter (4/4),
both guards, **54 tests at ~99% coverage**. At **P0 complete** (`docs/build-plan.md`).

## Next

- **Active handover → [Sprint 01](sprints/sprint-01-kernel-runtime.md)** — in-process
  bus + `AgentBase`, assigned to a coding agent on branch `sprint-01-kernel-runtime`.
  Implementation is handed off; the planning agent owns the PRD, build plan, sprint
  plans, and this file. See [docs/sprints/](sprints/README.md).
- After it: persistence + Neo4j adapters, distributed (Celery) bus, observability/
  metrics adapter, MCP binding, then **P2 — first vertical slice**
  (`provider → scanner → analyst`).

## Workflow

The planning agent (expensive) writes sprint handovers and maintains documentation
and progress; a coding agent (cheap) implements one active sprint at a time on its
own branch and hands back. See `docs/sprints/README.md`.

## Parked

- (none)

## Shipped

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
