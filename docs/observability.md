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

## 2a. Pipeline observatory — the human checker-that-prints

For a human's-eye view of **one run** — what each stage received (from whom) and produced, with the
floor/ceiling/required invariants flagged — use the **pipeline observatory** (`orchestration/observatory.py`
substrate + `orchestration/packs/trading_observatory.py` trading pack; DL-27). It applies the deliberation
firewall pattern (baseline + floor/ceiling) to the data pipeline.

- **Run a test + monitor it in one command:** `PYTHONPATH=. python scripts/run_local.py --real --observe`
  (live Aura + Tiingo; `--observe` alone is the in-memory demo, no creds). *Validated live against the free
  Aura (`c3ce91d0`) on 2026-06-25:* a 3-ticker run pulled 41 real Tiingo bars/name, opened 1 position
  (`AAPL qty=34 est=$293.32`), and reported `OBSERVATORY OK - all invariants hold`.
- **Monitor a persisted run after the fact:** `PYTHONPATH=. python scripts/observatory.py --run-id <id>`
  (reads the run back from Neo4j).

It prints the full `provider → reporter` spine, each stage as `[stage]  <- (trigger)` with its output
artifacts, and flags:

- **floor/ceiling** value breaches — e.g. `WARN returned: 0 < floor 1.0`, `WARN scored: 0 < floor 1.0`;
- **required** structural locks — a field that must be present (execution/monitor/reporter);
- **NOT REACHED** — a stage that should exist but does not (the chain broke).

Green `OK - all invariants hold` when healthy; the headline counts the WARNs. The committed invariant set
*is* the baseline ("what must be there"); the mechanism is domain-agnostic **substrate**, the invariants
are the trading **pack** (ADR-0012). `batch_trace` / `scripts/trace_run.py` print the same per-stage
numbers *without* the checks. *Next (DL-27): freeze a golden run + diff; promote `WARN`→`FAIL` as a gate.*

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
