# Observability & Historical Data

**Principle:** the system is loud *inward* and quiet *outward*. Internally it
captures rich metrics, traces, and a complete decision history; the operator sees
calm dashboards and concise summaries, drilling down only when they choose to.

Observability has three layers, with distinct retention and tools.

## 1. Live metrics & traces — Prometheus + Grafana

The kernel exposes an observability adapter that every agent emits through (no
agent talks to a metrics backend directly — it is plumbing). Instrumentation
covers, per agent and per capability:

- throughput (messages handled), latency, and queue depth;
- outcome counts (recommendations, approvals, rejections, fills, exits);
- **fault rate by `source_agent` / `severity`** (fed from the central fault channel);
- the top-level trust indicators (silent-failure rate, explainability coverage,
  quiet-operation rate, shadow-proof freshness).

Metrics are scraped by **Prometheus**; traces follow the OpenTelemetry convention.
**Grafana** is the visualization surface, with dashboards for:

- **System health** — run status, pipeline stage timings, active incidents.
- **Agent throughput & latency** — per-agent and per-capability.
- **Faults** — rate and breakdown by originating module, linked to incidents.
- **Trust indicators** — the PRD's operating-progress metrics over time.

Grafana is an *internal* operator/forensic surface. It does not replace the product
dashboard (which renders decisions, approvals, and narrative); it sits beside it
for time-series health.

## 2. Decision & event history — Neo4j + the relational store

The durable record of *what the system did and why* is not in the metrics stack:

- **Neo4j (provenance graph)** is the historical decision record —
  `Candidate → Recommendation → OrderIntent → Fill → Outcome` plus message lineage
  and faults — queryable for any past state, and the source the curator agent draws
  on for training datasets.
- **The relational store** holds append-only transactional history (orders,
  positions, approvals, audits, the fault table) for ACID, exportable evidence.

## 3. Logs

Structured logs carry the same `correlation_id` and `source_module` as faults and
metrics, so a metric spike, an incident, and the underlying log line all join up.
Aggregation (e.g. Loki) is optional and additive.

## Retention & history

- Metrics: short/medium retention in Prometheus for trend dashboards.
- Decisions & audits: long-lived and append-only in Neo4j + the relational store;
  retention windows, if any, are declared in configuration and audited when they
  trim (no silent deletion).
- Everything is exportable as a machine-parseable bundle for any date range.

## Build phase

The metrics adapter ships with the kernel runtime; Prometheus + Grafana
provisioning and the dashboard set land in the observability phase of
`docs/build-plan.md`. The historical stores (Neo4j + relational) land with the
persistence layer.
