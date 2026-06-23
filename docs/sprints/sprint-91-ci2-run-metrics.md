# Sprint 91 — CI-2: RunMetrics on the graph

**Branch:** `sprint-91-ci2-run-metrics`
**Status:** queued · **Phase:** P16 (continuous improvement, ADR-0013) · **Effort: M**

## Goal

Every run leaves a durable, queryable **measurement** on the provenance graph, keyed so it can later be
attributed to the parameter set that produced it. (Layer 2 of ADR-0013.) First producer: ingest.

## Scope

**In:**
- `RunMetrics` graph node: `{process, parameter_set_id (nullable for now), run_id, as_of, metric_name,
  value, unit, created_at}`; edge `MEASURES` from `RunMetrics` → the run/snapshot node it scores.
- A writer in `kernel`/provider that records ingest metrics from the batch: **degradation rate**
  (clean pillars / total), **fetch seconds**, **returned/requested**, **stale count**, **chunk count**.
- Reuse: forecaster IC scorecard and curator confusion matrix emit `RunMetrics` instead of bespoke
  shapes (adapter, no logic change).
- A surface query: `metrics --run <id>` and `metrics --process ingest --since <date>`.

**Out:** no experiments/promotion; Prometheus stays the live plane (RunMetrics is the durable per-run
record — note the split in the module header per ADR-0003).

## Deliverables

- `RunMetrics` node + `MEASURES` edge + writer; ingest metrics populated end-to-end.
- Scorecard → RunMetrics adapters (forecaster, curator).
- Surface query + tests (100% coverage).

## Acceptance

- A `run_local --real` ingest run writes `RunMetrics` rows; `metrics --run <id>` shows them.
- Degradation rate matches the trace (e.g. DL-17 run 2 = 0 Finnhub degraded → rate reflects it).
- `make ci` green.

## Dependencies

- Independent of CI-1, but pairs with it. Blocks CI-4 (compare reads RunMetrics).
