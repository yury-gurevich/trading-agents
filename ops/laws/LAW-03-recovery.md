# LAW-03 · Recovery — every action is recoverable or flagged

> The guarantee that you can always get back to a known-good state — or that you were
> warned, in writing, before you couldn't.

## Statement

Every action is **either reversible (has a rollback) or a declared Point of No Return**.
There is no third category. An action whose reversibility is *unknown* may not run.

## Clauses

- **RC-01 · Snapshot before destruction.** Any action that deletes or mutates shared state
  first captures a state snapshot (inventory / export) to a known location.
- **RC-02 · Rollback for the reversible.** Reversible actions declare the exact steps to
  undo them. "Rollback: redeploy with prior image" is valid; "rollback: unknown" is not.
- **RC-03 · PNR for the irreversible.** Irreversible actions are listed in
  `maintenance/points-of-no-return.md`, and `LAW-04` requires an interactive confirmation
  showing blast radius before they run.
- **RC-04 · Backups are defined and tested.** Each department declares what is backed up,
  where, RPO (max data loss) and RTO (max downtime). A backup never tested is assumed
  broken until a restore drill proves it.
- **RC-05 · Fail safe, not forward.** On failure: **stop**, preserve evidence, attempt the
  declared rollback, and report. Never blindly auto-retry a destructive step. Never
  "push through" a partial failure to finish.
- **RC-06 · Recoverability is a gate.** If RC-01..05 cannot be satisfied for an action, the
  action does not proceed — it is escalated to the operator as a decision (`LAW-05`).

## Relationship to the others

`LAW-02` decides *did it work*; `LAW-03` decides *can we undo it / get back*. Together they
mean: we never end up somewhere we can't explain (`LAW-05`) or can't leave.
