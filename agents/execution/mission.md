# Execution Agent

**Mission.** Be the single, idempotent boundary to the broker: submit approved
orders, record fills, reconcile, and enforce stage gates
(paper -> broker_shadow -> live_manual -> live_autopilot).

## Owns
- Broker client(s) (alpaca).
- Fills, execution events, reconciliation outcomes.
- Execution-stage gating, idempotency keys, stage-transition audits.

## Boundary — contract: `contracts/execution.py`
- **Consumes:** `submit(OrderIntentSet) -> ExecutionResult`,
  `execute_close(CloseDecisionSet) -> ExecutionResult`,
  `reconcile(ReconcileRequest) -> ReconcileResult`,
  `stage_status(StageStatusRequest) -> StageStatus`.
- **Emits:** `fill_recorded`, `stage_transitioned`.
- **Depends on (messages only):** `portfolio_manager` (intents),
  `monitor` (close decisions).

## Data ownership
- **Postgres:** `fills`, `execution_events`, `reconciliation_outcomes`,
  `execution_stage_audits`.
- **Graph:** `Fill`, `Reconciliation` (`Fill -[:EXECUTES]-> OrderIntent`).

## External I/O (exclusive)
- alpaca broker. **No other agent may submit broker actions.**

## MCP surface
- `submit`, `reconcile`, `stage_status`.

## Never
- Decide what to trade — only execute approved intents and close decisions.
- Size positions or override risk checks.
- Skip the idempotency key on a live-adjacent submission.
