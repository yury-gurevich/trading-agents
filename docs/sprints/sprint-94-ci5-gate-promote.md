# Sprint 94 — CI-5: gate + promote

**Branch:** `sprint-94-ci5-gate-promote`
**Status:** queued · **Phase:** P16 (continuous improvement, ADR-0013) · **Effort: M**

## Goal

Promote a challenger ParameterSet to champion **only** when it beats the champion on the target metric
with **no regression** on declared guardrails — then deliver it to agents. (Layer 4 of ADR-0013;
generalises the ADR-0010 eval-gate from prompts to any parameter set.)

## Scope

**In:**
- Guardrail spec on a `ParameterSet`/`Experiment`: `{target_metric, direction, min_delta,
  guardrail_metrics: [{name, max_regression}]}`.
- Gate evaluator over an `Experiment`'s RunMetrics: pass iff target improves ≥ `min_delta` and every
  guardrail stays within `max_regression`.
- Promotion: flip challenger → `champion`, demote old champion → `retired`; record a `Promotion` node
  (who/why/experiment ref) — provenance of the decision.
- Delivery: the active champion's overrides flow to agents via the existing **ACTIVATE config
  injection** (master entrypoints). Absorb ADR-0010's eval-gate: the operator prompt set is one
  ParameterSet whose metric is the golden-eval score.

**Out:** no automatic search (CI-6); promotion is triggered by an operator command on a passing
experiment.

## Deliverables

- Guardrail spec + gate evaluator + `Promotion` node + ACTIVATE delivery path.
- ADR-0010 eval-gate re-expressed as a CI-5 instance (no second mechanism).
- Tests (100% coverage): pass, fail-on-regression, fail-on-insufficient-delta.

## Acceptance

- A passing experiment promotes the challenger and agents pick up the new set via ACTIVATE.
- A challenger that regresses a guardrail is refused with the offending metric named.
- `make ci` green.

## Dependencies

- CI-3 (ParameterSet), CI-4 (Experiment). Supersedes the bespoke ADR-0010 gate wiring.
