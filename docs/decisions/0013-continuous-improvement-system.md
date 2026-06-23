---
type: Architecture Decision
status: accepted
closes: "How do we stop hand-tuning parameters by guess-run-measure-re-run? How does every process get measured, every tunable get optimised against a metric, and improvements get promoted without regression — and where does the config/metrics state live?"
tags: [continuous-improvement, tunable, parameter-set, metrics, champion-challenger, quality-gate, provenance, p16]
---

# ADR-0013 — Continuous-improvement system: configurable parameters, measured runs, gated promotion

**Status:** Accepted
**Date:** 2026-06-24
**Deciders:** Operator

---

## Context

DL-17 tuned the ingest pacing (chunk size, delay, sigma) by hand: the operator read degradation
flags off a trace and edited `.env`. That is not a system — there is no record of what each value
scored, no comparison between alternatives, and no promotion gate. Every processing constant in the
codebase is already declared through `tunable()` (≈145 of them, bounded and justified), and several
processes already have bespoke scorecards (forecaster IC, curator confusion matrix, sentiment
champion–challenger / ADR-0010). The pieces of a feedback loop exist but are **siloed and manual**.

The operator's directive: parameters must be **configurable, not settable** — owned by a system that
measures, sweeps, and promotes them — and the whole map→measure→tune→improve loop must be built.

## Decision

Build a **continuous-improvement system** over four layers, with **all state on the Neo4j
provenance graph** (no new store; the graph already records every run):

1. **Catalogue** — `describe_all()` aggregates every agent's `tunable()` fields into one registry:
   the menu of what is tunable, with bounds and justification. Source of truth stays in code; the
   catalogue is derived.
2. **Measure** — each run writes a `RunMetrics` node keyed by `(process, parameter_set_id, run_id,
   as_of)`. Metrics are process-specific (ingest: degradation rate, fetch seconds, returned/requested;
   scanner: survivor realised-return; forecaster: IC; operator: eval-set score). Existing scorecards
   become RunMetrics producers rather than separate artifacts.
3. **Experiment** — a run loads a named, versioned **`ParameterSet`** node instead of ad-hoc env.
   Champion vs challenger sets are run against the **same `as_of`** so their RunMetrics are comparable.
4. **Gate** — a challenger is promoted only when its metric ≥ champion with no regression on declared
   guardrails. Promotion flips the active `ParameterSet` and is delivered to agents through the
   existing **ACTIVATE config injection** channel. The gate **generalises ADR-0010** from prompts to
   any parameter set — one mechanism, not two.

**Configurable, not settable:** `ParameterSet` is the unit of configuration. Env vars remain only as
the local-dev override; production reads the promoted set via ACTIVATE.

## Why all-on-the-graph

The provenance graph already stores every run's lineage, so `RunMetrics` attaches naturally to the
run it measures, and `ParameterSet → RunMetrics` becomes a queryable "which knobs produced which
outcome" lineage — the core asset of the loop. One store, no new infra, and the substrate-DB question
(DL-15, possible Cosmos move) can relocate it later without changing the model. The trade-off — param
history is not git-diffable — is accepted; the graph is versioned by node, and ADRs/design-log carry
the human-readable rationale.

## Consequences

- A new phase **P16** builds it in six sprints (**CI-1…CI-6 / S90–S95**); see the sprint specs.
- `tunable()` stays the single declaration point; nothing becomes a bare literal.
- ADR-0010's eval-gate is absorbed by the CI-5 gate (its golden-eval-set becomes the operator
  process's RunMetrics + guardrail). ADR-0002 sentiment champion–challenger becomes one instance of
  the general pattern.
- DL-09 (filter decisions as a training source) is subsumed by CI-2/CI-4 rather than built separately.

## Alternatives considered

- **Repo JSON for ParameterSets + graph for metrics** — git-diffable param history, but splits the
  loop's state across two stores and breaks the param→metric lineage query. Rejected.
- **Cosmos DB now (per DL-15)** — aligns with the substrate-DB direction but depends on DL-15 landing
  and adds setup before any measurement exists. Deferred; the graph model ports to it later.
- **Keep tuning by hand** — the status quo; does not scale past one knob and keeps no memory. Rejected.

## Open questions (resolved in the sprint specs)

- Metric plane overlap with Prometheus (ADR-0003): RunMetrics is the durable per-run record on the
  graph; Prometheus stays the live operational plane. CI-2 defines the split.
- Optimiser sophistication (CI-6): grid sweep first within `tunable` bounds, smarter search later.
