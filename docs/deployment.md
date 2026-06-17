# Deployment

> **Status: interim.** The current setup deploys all agents in a **single monolithic container**.
> This is a temporary shortcut. The accepted architecture (ADR-0007) is **one Docker image per
> agent**, orchestrated by a **master bootstrap agent**, running on Azure Container Apps. The
> per-agent split is tracked under the P14 milestone. The documentation below describes the
> current monolith deployment; it will be superseded when P14 ships.

Container deployment for the trading-agents app and its Prometheus observability sidecar.

## Files

| File | Purpose |
| --- | --- |
| `Dockerfile` | Python 3.13-slim image; entrypoint `surfaces.entrypoint` starts /metrics server then CLI |
| `docker-compose.yml` | App + Prometheus stack; works with both `docker compose up` and `docker stack deploy` |
| `infra/prometheus/prometheus.compose.yml` | Committed Prometheus config; scrapes `app:8000`; remote_write commented out |
| `infra/prometheus/prometheus.local.yml` | Generated config with Azure credentials; gitignored; enables remote_write to Azure Monitor |
| `infra/setup-prometheus-auth.ps1` | Generates `prometheus.local.yml` and writes Azure SP creds to `.env` |
| `infra/setup-azure.ps1` | Provisions Azure Monitor Workspace + Azure Managed Grafana |
| `infra/setup-grafana-datasource.ps1` | Wires Prometheus data source into Grafana and patches the dashboard |

## Prerequisites

1. **`.env` file** — copy `.env.example` and fill in `NEO4J_*` vars:

   ```bash
   cp .env.example .env
   # edit .env
   ```

2. **Prometheus config** — the committed `prometheus.compose.yml` scrapes metrics locally with no Azure creds. To enable remote_write to Azure Monitor, generate `prometheus.local.yml` first:

   ```powershell
   .\infra\setup-prometheus-auth.ps1
   ```

   Then point `configs.prometheus_config.file` in `docker-compose.yml` at `prometheus.local.yml`.

## Local dev

Start both services and tail logs:

```bash
make stack-up
# or
docker compose up
```

| Endpoint | URL |
| --- | --- |
| App `/metrics` | <http://localhost:8000/metrics> |
| Prometheus UI | <http://localhost:9090> |

Stop:

```bash
make stack-down
# or
docker compose down
```

## Swarm stack deploy

Build the image, initialise a single-node swarm if needed, then deploy:

```bash
make stack-deploy
# expands to:
docker build -t trading-agents:local .
docker swarm init           # skip if already a swarm node
docker stack deploy -c docker-compose.yml trading-agents
```

Remove the stack:

```bash
make stack-rm
# or
docker stack rm trading-agents
```

## Enabling Azure remote_write

The Swarm stack uses Docker `configs:` to inject the Prometheus config. To switch to the generated config with Azure credentials:

1. Generate `infra/prometheus/prometheus.local.yml`:

   ```powershell
   .\infra\setup-prometheus-auth.ps1
   ```

2. Update `docker-compose.yml` — change the last two lines under `configs:`:

   ```yaml
   configs:
     prometheus_config:
       file: ./infra/prometheus/prometheus.local.yml   # was prometheus.compose.yml
   ```

3. Re-deploy:

   ```bash
   docker stack deploy -c docker-compose.yml trading-agents
   ```

## Azure observability stack

| Component | Details |
| --- | --- |
| Azure Monitor Workspace | `trading-agents-monitor`, Australia East, resource group `trading-agents-prod` |
| Prometheus query endpoint | `https://trading-agents-monitor-bhg7e8avecgscecw.australiaeast.prometheus.monitor.azure.com` |
| Azure Managed Grafana | `https://trading-agents-grafana-hecpbea2b9cqckf2.eau.grafana.azure.com` |
| Dashboard | "Trading Agents — System Health" (`uid: trading-agents-main`) |
| Prometheus auth | Service principal `trading-agents-prometheus`; credentials in `.env` (gitignored) |

Provision from scratch:

```powershell
.\infra\setup-azure.ps1               # Azure Monitor Workspace + Grafana
.\infra\setup-prometheus-auth.ps1     # SP auth + prometheus.local.yml
.\infra\setup-grafana-datasource.ps1  # wire data source + patch dashboard
```

## Architecture

```text
┌─────────────────────────────┐
│  Docker stack: trading-agents│
│                              │
│  ┌──────────┐  :8000         │
│  │  app     │──/metrics      │
│  │          │                │
│  │ surfaces │                │
│  │.entrypoint               │
│  └──────────┘                │
│       ▲                      │
│       │ scrape app:8000      │
│  ┌────────────┐  :9090        │
│  │ prometheus │──UI           │
│  └────────────┘               │
│       │ remote_write          │
└───────┼──────────────────────┘
        ▼
  Azure Monitor Workspace
        │
  Azure Managed Grafana
```

The `observability` bridge network lets Prometheus reach the app by service name.
The app's health check on `/metrics` gates Prometheus startup via `depends_on: condition: service_healthy`.
