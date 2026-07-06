# Forecaster Agent

**Mission.** Provide advisory ML forecasts (exit timing, news impact, ...) as
clearly labelled shadow signals that never gate a decision until scorecards
prove they deserve promotion.

## Owns

- Shadow models and their prediction logs.
- Proof cycles and operator-facing scorecards.

## Boundary — contract: `contracts/forecaster.py`

- **Consumes:** `forecast`, `forecast_return`, `forecast_factor`,
  `scorecard`, `sentiment_scorecard`, and `return_scorecard`.
- **Emits:** `scorecard_refreshed`.
- **Depends on (messages only):** `provider` (features/data).

## Data ownership

- **Postgres:** `shadow_predictions`, `shadow_proof_cycles`, `model_scorecards`.
- **Graph:** `ShadowPrediction`, `Model` (`ShadowPrediction -[:ADVISES]-> ...`).

## External I/O

- None.

## MCP surface

- `forecast`, `scorecard`.

## Governed factor shadow loop

- Approve a `FactorProposal` after reviewing its S113 walk-forward evidence.
- Enable it by setting `FORECASTER_FACTOR_NAME` and `FORECASTER_FACTOR_PARAMS`
  in operator-controlled config; leave both empty to keep the feature off.
- The forecaster emits only `shadow=True` `ShadowPrediction`s under the factor
  model id; it never gates, sizes, or promotes.
- Review `scorecard` for the factor model id. Promote through existing
  registry/stage rails, or kill by clearing the setting.

## Never

- Emit a binding (non-shadow) signal.
- Gate or veto a recommendation, sizing, or exit.
- Self-promote a model without an operator-facing scorecard.

> Deliberately advisory — keeps the system deterministic-by-default; ML earns
> trust through measured scorecards before it ever influences a hard decision.
