---
type: Architecture Decision
status: accepted
closes: "What is the approved infrastructure list? Can we add Prometheus, Celery, Postgres, or Grafana?"
tags: [azure, infrastructure, stack, prometheus, celery, postgres]
---

# ADR-0009 — Azure-native infrastructure standard

**Status:** Accepted  
**Date:** 2026-06-19  
**Deciders:** Operator

---

## Context

The trading-agents system runs on Azure Container Apps with Log Analytics, Azure Monitor,
and Azure Managed Prometheus already provisioned (see `.env`: `AZURE_CA_ENV_NAME`,
`AZURE_MONITOR_CONNECTION_STRING`, `PROMETHEUS_REMOTE_WRITE_URL`). Prior decisions
(ADR-0003, ADR-0005, ADR-0007) each chose an Azure service for a specific role. What
was missing was a single governing rule that makes the pattern explicit and enforceable.

Three infrastructure components carried over from the bootstrap era without a clear
retirement date:

1. **Local Prometheus + Grafana** — docker-compose sidecar and `infra/prometheus/`,
   `infra/grafana/` configs. The metrics pipeline already pushes to Azure Managed
   Prometheus via `prometheus-client` remote-write. The local sidecar was never opened
   in normal operation.

2. **RabbitMQ** (ADR-0004) — superseded by ADR-0005 (Azure Service Bus) before it was
   ever deployed. The `DEP-BUS` dependency charter still referenced ADR-0004 and
   "AMQP/RabbitMQ" — dead scaffolding.

3. **CeleryBus** — a transitional in-process bus that defaults to `memory://` (no broker,
   eager mode). DRIFT-008 resolved inter-agent comms to Azure Service Bus. Celery is
   holding the seat.

## Decision

**All infrastructure is Azure-native.** The approved services for each role are
enumerated in `docs/laws/stack.md` (the governing charter document).

Two explicit exceptions:

1. **Neo4j** — no Azure-managed property graph with APOC + GDS exists; Neo4j is the
   permanent graph-store exception until a future ADR supersedes it.
2. **External SaaS vendors** (Tiingo, Alpaca, Finnhub, AV, FMP, FRED, HuggingFace,
   Postgres) — governed by DEP-FEED / DEP-BROKER, not by the Azure-native rule.

Transitional components (CeleryBus, in-process `MessageBus`) are allowed until their
Azure-native replacements ship. Retirement is coordinated (code + tests + deps), not
ad-hoc hygiene.

## Consequences

### Immediate (this decision)

- **Local Prometheus / Grafana retired.** `infra/prometheus/`, `infra/grafana/`,
  `infra/setup-prometheus-auth.ps1`, `infra/setup-grafana-datasource.ps1` moved to
  the `trading-agent-del/` staging area. The Prometheus service is removed from
  `docker-compose.yml`. The `prometheus-client` library stays — it is the SDK that
  remote-writes metrics to Azure Managed Prometheus.
- **`DEP-BUS` dependency charter updated** — "AMQP/RabbitMQ later, ADR-0004" corrected
  to "Azure Service Bus later, ADR-0005; transitional CeleryBus retires at P14."
- **ADR-0004 is superseded** by ADR-0005 (already the case; now formally noted here).

### Deferred (P14)

- `CeleryBus` and `redis` dependency retire when `ServiceBusBus` ships.
- `SERVICEBUS_CONNECTION_STRING` and `EVENTHUBS_CONNECTION_STRING` (currently commented
  in `.env`) become required keys at that point.

### Permanent

- Any proposed new infrastructure component that is not an Azure-managed service, not
  Neo4j, and not an approved SaaS vendor requires a new ADR before code is written.

## Alternatives considered

**Keep local Prometheus for offline dev.** Rejected: the metrics remote-write path
(`prometheus-client` → Azure Managed Prometheus) is the one that matters for
correctness. Running a local Prometheus sidecar tests a scrape path that no longer
reflects the deployed architecture.

**Replace Neo4j with Azure Cosmos DB (Gremlin).** Rejected: Cosmos Gremlin does not
support APOC procedures or the Graph Data Science library, which are load-bearing for
the planned graph analytics. Neo4j remains as the explicit exception.
