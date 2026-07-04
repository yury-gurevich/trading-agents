# Layer-0 — Technology stack charter

**Ratified 2026-06-19.** This is the governing constraint for all infrastructure choices.
See ADR-0009 for the full decision record and rationale.

## Rule 1 — Azure-native infrastructure

All infrastructure **must** run on Azure-managed services. No self-hosted servers in
production or in the deployed Container Apps environment.

| Role | Approved Azure service |
| --- | --- |
| Compute | Azure Container Apps (scale-to-zero) |
| Inter-agent bus | Azure Service Bus (claim-check pattern, ADR-0005) |
| Log plane | Azure Event Hubs → Log Analytics (ADR-0003) |
| Metrics | Azure Managed Prometheus + Azure Monitor |
| Observability UI | Azure Monitor Workbooks / dashboards |
| Secrets | Azure Key Vault (master agent is sole accessor, ADR-0007) |
| Container registry | Docker Hub → Azure Container Apps pull |

## Rule 2 — Neo4j is the sanctioned graph-store exception

Neo4j is **not** replaced by an Azure-managed database. Azure has no equivalent for a
property graph with APOC + GDS. This exception is explicit and permanent until superseded
by a future ADR.

- Dev/eval: local Docker Enterprise (`infra/neo4j/local/`, named db `traiding-agents`)
- Production: TBD (Neo4j AuraDS or self-managed on AKS — pending scale decision)
- Governed by DEP-NEO4J (dependencies.md) and ADR-0001, ADR-0008.

## Rule 3 — External SaaS vendors are a separate category

Market-data and broker vendors are governed by DEP-FEED and DEP-BROKER, not by
Rule 1. They are third-party SaaS accessed over the internet — the Azure-native rule
does not apply.

| Vendor | Role |
| --- | --- |
| Alpaca | Paper/live broker + runtime/batch OHLCV |
| Tiingo | Cheap OHLCV fallback + raw-history/evidence source when DL-37 lineage is required |
| Finnhub | Fundamentals + news |
| Alpha Vantage | Vendor news sentiment (challenger, ADR-0002) |
| FMP | Validation sub-universe (~87 symbols) |
| FRED | Macro/regime inputs |
| HuggingFace | FinBERT model weights (forecaster, advisory) |

## Rule 4 — Bootstrap technology retires when its replacement ships

Transitional components are allowed while their Azure-native replacement is under
construction. They **must not** be treated as permanent. Retirement is a coordinated
change (code + tests + deps + CI together) — never ad-hoc hygiene.

| Transitional | Retirement trigger | Target |
| --- | --- | --- |
| `CeleryBus` / `InProcessBus` | Azure Service Bus adapter ships (P14) | `ServiceBusBus` |
| `prometheus-client` local dev | Azure Managed Prometheus fully proven green | Keep as SDK; only sidecar retires |

## What is explicitly retired by this charter

- Local Prometheus server (docker-compose sidecar) — superseded by Azure Managed Prometheus
- Local Grafana dashboards — superseded by Azure Monitor
- RabbitMQ (ADR-0004, superseded by ADR-0005 before it was ever deployed)

## Violation procedure

Any proposed addition that is not an Azure-managed service, not Neo4j, and not an
approved SaaS vendor requires a new ADR **before** any code is written. The stack is
intentionally narrow; new entries are the exception, not the rule.
