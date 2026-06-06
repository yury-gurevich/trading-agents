# Portfolio Manager Agent

**Mission.** Decide which recommendations become sized, risk-checked orders under
current policy and portfolio state, and record exactly why each was approved or
rejected.

## Owns
- Position sizing.
- Risk checks (exposure, correlation, caps, cash).
- The approval decision and the approval queue.
- Portfolio policy state.

## Boundary — contract: `contracts/portfolio_manager.py`
- **Consumes:** `evaluate_orders(RecommendationSet) -> OrderIntentSet`,
  `explain_decision(RecommendationSet) -> Explanation`.
- **Emits:** `orders_decided`.
- **Depends on (messages only):** `analyst`, `provider` (regime/policy),
  `forecaster` (optional advisory).

## Data ownership
- **Postgres:** `portfolios`, `order_intents`, `pm_configs`, `approval_queue`.
- **Graph:** `PMRun`, `OrderIntent` (`OrderIntent -[:APPROVES]-> Recommendation`).

## External I/O
- None.

## MCP surface
- `evaluate_orders`, `explain_decision`.

## Never
- Talk to the broker directly — hand approved intents to `execution`.
- Call a market-data API directly.
- Promote an execution stage — that is execution's gated authority.
