# LAW-02 · Successful Execution — what "done" means

> An operation is not "done" because a script exited 0. Success is **proven**, not assumed.

## Statement

An action has **succeeded** only when *every* condition below holds. If any fails, the
action has **failed** — even if no error was thrown — and `LAW-03` (Recovery) takes over.

## The success contract (all must hold)

- **SE-01 · Gates passed.** Every required preflight gate was GREEN before the action ran.
- **SE-02 · Postcondition proven.** The action's declared postcondition was *verified* by an
  independent check (e.g. the node exists in the graph; the app answers health) — not the
  exit code. No postcondition → not a real action.
- **SE-03 · No partial state.** No orphaned, half-created, or dangling resources. Partial =
  failure. The system is in a *named, known* state (the one the runbook predicted).
- **SE-04 · Within budget.** Cost stayed within the action's declared guard; an overage is a
  failure that must be surfaced (`LAW-04`), not silently absorbed.
- **SE-05 · Recorded.** A ledger row was written with outcome, duration, cost, and the
  postcondition evidence — so success is *defendable* (`LAW-05`).
- **SE-06 · Idempotent convergence.** Re-running the action from the new state is a no-op (it
  converges), proving the result is stable, not accidental.

## Corollaries

- **Partial success is failure.** There is no "mostly worked". Half a fleet deployed is a
  failed deploy that must roll back or be explicitly accepted as a known degraded state.
- **Silent success is failure.** If it can't be shown (SE-02/SE-05), it didn't happen.
- **Definition of Done is per-action**, declared in the charter's `OPS-ACT` postcondition
  column. This law is the *shape*; each charter fills the *specifics*.
