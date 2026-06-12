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

## 2. Decision & event history — Neo4j

The durable record of *what the system did and why* is not in the metrics stack:

- **Neo4j (the single store)** is the historical decision record —
  `Candidate → Recommendation → OrderIntent → Fill → Outcome` plus message lineage
  and faults — queryable for any past state, and the source the curator agent draws
  on for training datasets.
- It also holds the append-only **transactional history** (orders, positions,
  approvals, audits, faults) as nodes with ACID guarantees — exportable evidence
  without a separate relational store (`docs/decisions/0001-neo4j-primary-store.md`).

## 3. Logs

Structured logs carry the same `correlation_id` and `source_module` as faults and
metrics, so a metric spike, an incident, and the underlying log line all join up.
Aggregation (e.g. Loki) is optional and additive.

## Retention & history

- Metrics: short/medium retention in Prometheus for trend dashboards.
- Decisions & audits: long-lived and append-only in Neo4j;
  retention windows, if any, are declared in configuration and audited when they
  trim (no silent deletion).
- Everything is exportable as a machine-parseable bundle for any date range.

## Deployed stack

| Component | Where |
| --- | --- |
| Prometheus metrics adapter | `kernel/metrics_prometheus.py` |
| /metrics HTTP server | `surfaces/metrics_server.py` (WSGI, port 8000) |
| Container entrypoint | `surfaces/entrypoint.py` |
| Azure Monitor Workspace | `trading-agents-monitor`, Australia East |
| Azure Managed Grafana | `https://trading-agents-grafana-hecpbea2b9cqckf2.eau.grafana.azure.com` |
| Dashboard | "Trading Agents — System Health" (uid: `trading-agents-main`) |
| Prometheus config template | `infra/prometheus/prometheus.yml` |
| Auth setup script | `infra/setup-prometheus-auth.ps1` |

### Running locally

```bash
docker compose up
```

Requires:

- `.env` file with `NEO4J_*` vars (copy from `.env.example`)
- `infra/prometheus/prometheus.local.yml` — generate with `.\infra\setup-prometheus-auth.ps1`

Access:

- `/metrics` endpoint: `http://localhost:8000/metrics`
- Prometheus UI: `http://localhost:9090`
- Grafana: see URL in table above

### Dashboard panels

1. Request rate (req/s) — `trading_agents_kernel_requests_total`
2. Error rate (%) — ratio of failed to total requests
3. P99 latency (s) — `trading_agents_kernel_request_latency_seconds`
4. P50 latency (s)
5. Faults by severity — `trading_agents_kernel_faults_total{severity="..."}`
6. Faults by agent — same metric broken out by `agent` label
7–10. (additional panels for throughput and agent breakdown)
