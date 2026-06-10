# Portfolio Manager Agent

**Mission.** Decide which recommendations become sized, risk-checked orders under
current policy and portfolio state, and record exactly why each was approved or
rejected.

## Owns

- Position sizing.
- Risk checks (caps, cash, minimum quantity).
- The approval decision.
- Portfolio policy state. A fresh paper portfolio is sourced from settings until
  execution/monitor own real positions later in P3.

## Boundary — contract: `contracts/portfolio_manager.py`

- **Consumes:** `evaluate_orders(RecommendationSet) -> OrderIntentSet`,
  `explain_decision(RecommendationSet) -> Explanation`.
- **Emits:** `orders_decided`.
- **Depends on (messages only):** `analyst`, `provider` (regime/policy),
  `forecaster` (optional advisory).

## Data ownership

- **Graph:** `PMRun`, `OrderIntent` (`OrderIntent -[:APPROVES]-> Recommendation`).
- **Money discipline:** payloads carry `Money`/`Decimal`; graph properties store
  monetary amounts as integer cents per ADR-0001.

## External I/O

- None.

## MCP surface

- `evaluate_orders`, `explain_decision`.

## Never

- Talk to the broker directly — hand approved intents to `execution`.
- Call a market-data API directly.
- Promote an execution stage — that is execution's gated authority.
