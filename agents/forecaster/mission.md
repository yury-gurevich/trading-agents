# Forecaster Agent

**Mission.** Provide advisory ML forecasts (exit timing, news impact, ...) as
clearly labelled shadow signals that never gate a decision until scorecards
prove they deserve promotion.

## Owns

- Shadow models and their prediction logs.
- Proof cycles and operator-facing scorecards.

## Boundary — contract: `contracts/forecaster.py`

- **Consumes:** `forecast(ForecastRequest) -> ShadowPrediction`,
  `scorecard(ScorecardRequest) -> Scorecard`.
- **Emits:** `scorecard_refreshed`.
- **Depends on (messages only):** `provider` (features/data).

## Data ownership

- **Postgres:** `shadow_predictions`, `shadow_proof_cycles`, `model_scorecards`.
- **Graph:** `ShadowPrediction`, `Model` (`ShadowPrediction -[:ADVISES]-> ...`).

## External I/O

- None.

## MCP surface

- `forecast`, `scorecard`.

## Never

- Emit a binding (non-shadow) signal.
- Gate or veto a recommendation, sizing, or exit.
- Self-promote a model without an operator-facing scorecard.

> Deliberately advisory — keeps the system deterministic-by-default; ML earns
> trust through measured scorecards before it ever influences a hard decision.
